# Code Review Report: Discovery Module

**Review Date:** 2026-02-03
**Reviewer:** Claude Code
**Scope:** `amplify.ai_1/discovery` - Backend services, repositories, middleware, and frontend API services
**Status:** FIXES APPLIED (2026-02-03)

---

## Executive Summary

The Discovery module implements LOB-aware smart upload matching for workforce data, mapping job titles to O*NET occupations with industry context. The codebase is generally well-structured with good separation of concerns and comprehensive exception handling. However, several issues were identified that should be addressed to improve robustness, security, and maintainability.

**Critical Issues:** 2 (FIXED)
**High Priority Issues:** 5 (FIXED)
**Medium Priority Issues:** 8
**Low Priority Issues:** 4
**Security Issues:** 2 (FIXED)

---

## 1. Bugs/Defects

### CRITICAL: Transaction Corruption in `lob_mapping_repository.py` - FIXED

**File:** `app/repositories/lob_mapping_repository.py`
**Lines:** 66-71
**Status:** FIXED

**Issue:** The `find_fuzzy` method catches a broad `Exception` and attempts to continue without rolling back the session. When pg_trgm is not installed, this corrupts the database session, causing all subsequent queries in the same transaction to fail with `InFailedSQLTransactionError`.

**Fix Applied:**
1. Added explicit rollback before fallback: `await self.session.rollback()`
2. Now catches specific exceptions `ProgrammingError` or `OperationalError` instead of bare `Exception`
3. Added logging to warn when falling back due to pg_trgm unavailability

---

### HIGH: Fuzzy Match Still Called Despite Removal in Service - FIXED

**File:** `app/services/lob_mapping_service.py`
**Lines:** 63-64
**Status:** FIXED

**Issue:** The comment says fuzzy match was removed, but the `lob_mapping_repository.py` still has the `find_fuzzy` method which can be called from other code paths. The repository method is still dangerous without pg_trgm.

**Fix Applied:**
1. Repository `find_fuzzy` method now has proper rollback and specific exception handling
2. Service correctly bypasses fuzzy match (as documented)

---

### HIGH: Missing Column Validation in `file_parser.py` - FIXED

**File:** `app/services/file_parser.py`
**Lines:** 125-126
**Status:** FIXED

**Issue:** The `extract_unique_values` method does not validate that the requested `column` exists in the DataFrame. This will raise a `KeyError` with a potentially confusing error message.

**Fix Applied:**
1. Added column existence check before accessing DataFrame
2. Raises `FileParseException` with descriptive message listing available columns if column not found
3. Added safe extension extraction using `pathlib.Path`

---

### MEDIUM: Potential Memory Issue with Large Files

**File:** `app/services/file_parser.py`
**Lines:** 43-46

```python
if ext == "csv":
    df = pd.read_csv(io.BytesIO(content))
elif ext in ("xlsx", "xls"):
    df = pd.read_excel(io.BytesIO(content))
```

**Issue:** Entire file is loaded into memory twice (once as bytes, once as DataFrame). For large workforce files, this could cause memory exhaustion.

**Remediation Plan:**
1. Consider streaming CSV parsing for large files
2. Add file size validation before parsing
3. Use chunked reading for files above a threshold (e.g., 10MB)

---

## 2. Logging Issues

### HIGH: Missing Logging in Critical Paths - FIXED

**File:** `app/repositories/lob_mapping_repository.py`
**Lines:** 69-71
**Status:** FIXED

**Issue:** The fallback from fuzzy match to exact match happens silently. When pg_trgm fails, there's no logging to indicate the degraded functionality.

**Fix Applied:**
1. Added `logger.warning()` when falling back due to pg_trgm unavailability
2. Includes pattern and exception details for debugging

---

### MEDIUM: No Logging in S3 Operations - FIXED

**File:** `app/services/s3_client.py`
**Lines:** 37-65, 67-78, 80-91, 93-107
**Status:** FIXED

**Issue:** S3 operations (upload, download, delete, exists) have no logging. Failures in `file_exists` are silently swallowed.

**Fix Applied:**
1. Added `logger.debug()` for all successful operations with size info
2. Added `logger.error()` for non-404 failures in `file_exists`
3. Now catches `ClientError` specifically and re-raises non-404 errors

---

### MEDIUM: Inconsistent Log Levels

**File:** `app/services/llm_service.py`
**Lines:** 96-106

```python
logger.error(f"Authentication error: {e}")  # error
logger.warning(f"Rate limit exceeded: {e}")  # warning
logger.error(f"Connection error: {e}")       # error
logger.error(f"API error: {e}")              # error
```

**Issue:** Rate limit is logged as `warning` while other recoverable errors are `error`. Rate limits are expected in production and should be `info` or `debug`, while auth errors that may indicate misconfiguration should stay `error`.

**Remediation Plan:**
1. Change rate limit logging to `info` level
2. Add request context (method, endpoint) to log messages
3. Consider structured logging with consistent fields

---

### LOW: Missing Request Context in Error Handlers

**File:** `app/middleware/error_handler.py`
**Lines:** 193-194

```python
logger.exception(f"Unhandled exception: {exc}")
```

**Issue:** Unhandled exceptions are logged without request context (path, method, user ID, session ID).

**Remediation Plan:**
1. Add `request.url.path` and `request.method` to log messages
2. Consider adding correlation ID for request tracing

---

## 3. Error Handling

### HIGH: Bare Exception Catch in S3 Client - FIXED

**File:** `app/services/s3_client.py`
**Lines:** 102-107
**Status:** FIXED

**Issue:** Catching bare `Exception` hides real errors like network timeouts, authentication failures, or bucket access issues. All are treated as "file not found".

**Fix Applied:**
1. Now catches `botocore.exceptions.ClientError` specifically
2. Checks for error code `404` to return False for "not found"
3. Re-raises all other exceptions with logging

---

### HIGH: Missing Error Handling for LLM JSON Parsing - FIXED

**File:** `app/services/lob_mapping_service.py`
**Lines:** 138-144
**Status:** FIXED

**Issue:** The broad `Exception` catch masks all LLM errors. If the LLM is misconfigured or rate-limited, this silently returns `None` instead of propagating the error.

**Fix Applied:**
1. Now catches `json.JSONDecodeError` separately with logging
2. Allows LLM exceptions (`LLMError` and subclasses) to propagate
3. Added NAICS code format validation
4. Added input validation for LOB patterns (max length, control chars)

---

### MEDIUM: No Validation for NAICS Codes Format

**File:** `app/services/lob_mapping_service.py`
**Lines:** 141

```python
if isinstance(codes, list) and all(isinstance(c, str) for c in codes):
    return codes
```

**Issue:** NAICS codes are validated only as strings. Invalid formats like empty strings, non-numeric codes, or codes with wrong lengths are accepted and stored.

**Remediation Plan:**
1. Add NAICS code format validation (2-6 digit numeric codes)
2. Filter out invalid codes before caching
3. Log warnings for invalid codes received from LLM

---

### MEDIUM: Missing Not Found Handling in Role Mapping Service

**File:** `app/services/role_mapping_service.py`
**Lines:** 85-87

```python
content = await self.upload_service.get_file_content(upload_id)
if not content:
    return []
```

**Issue:** When file content is not found, an empty list is returned silently. This could mask S3 connectivity issues or deleted files.

**Remediation Plan:**
1. Distinguish between "file not found" and "empty file"
2. Raise appropriate exception for missing files
3. Log the reason for returning empty results

---

## 4. Robustness Issues

### HIGH: No Input Sanitization for LOB Patterns

**File:** `app/services/lob_mapping_service.py`
**Lines:** 51, 69, 103-112

**Issue:** LOB patterns from user input are passed directly to SQL queries after only lowercase/strip normalization. While SQLAlchemy provides parameterization, extremely long inputs could cause performance issues.

**Remediation Plan:**
1. Add maximum length validation for LOB patterns (e.g., 255 chars)
2. Add character validation to reject control characters
3. Consider rate limiting on the `/lob/lookup` endpoint

---

### MEDIUM: Race Condition in LLM Result Caching

**File:** `app/services/lob_mapping_service.py`
**Lines:** 68-73

```python
await self.repository.create(
    lob_pattern=normalized,
    naics_codes=naics_codes,
    confidence=0.8,
    source="llm",
)
```

**Issue:** When multiple requests for the same unknown LOB arrive concurrently, each will call the LLM and try to create a cache entry, potentially causing duplicate entries or unique constraint violations.

**Remediation Plan:**
1. Use `INSERT ... ON CONFLICT DO NOTHING` for cache writes
2. Or add distributed locking for LLM calls per normalized pattern
3. Or accept duplicate LLM calls and use `bulk_upsert` instead of `create`

---

### MEDIUM: No Timeout for LLM Calls

**File:** `app/services/lob_mapping_service.py`
**Lines:** 139

```python
response = await self.llm.complete(prompt)
```

**Issue:** LLM calls have no explicit timeout. A slow LLM response could block the request indefinitely.

**Remediation Plan:**
1. Add timeout parameter to LLM service calls
2. Use `asyncio.timeout()` or `asyncio.wait_for()` wrapper
3. Configure timeout based on endpoint requirements (e.g., 30s for batch, 10s for lookup)

---

### LOW: Missing Connection Pool Configuration

**File:** `app/services/s3_client.py`
**Lines:** 22

```python
self._session = aioboto3.Session()
```

**Issue:** Each S3Client instance creates a new session. In high-concurrency scenarios, this could exhaust connection pools.

**Remediation Plan:**
1. Share aioboto3.Session across S3Client instances
2. Configure connection pool size in settings
3. Consider using a singleton pattern for the S3 session

---

### LOW: File Extension Detection Vulnerability

**File:** `app/services/file_parser.py`
**Lines:** 40-41

```python
ext = filename.lower().split(".")[-1]
```

**Issue:** This can be bypassed with filenames like `malicious.csv.exe` (would detect "exe") or files without extensions (would use the full filename).

**Remediation Plan:**
1. Use `pathlib.Path(filename).suffix` for proper extension extraction
2. Validate that extension is in allowed list before processing
3. Consider checking file magic bytes in addition to extension

---

## 5. Security Issues

### HIGH: No File Size Limit Enforcement - FIXED

**File:** `app/services/upload_service.py`
**Lines:** 24-71
**Status:** FIXED

**Issue:** There's no visible file size validation in the upload service. Large files could cause denial of service through memory exhaustion.

**Fix Applied:**
1. Added file size validation before parsing (default max 50MB)
2. Added `max_upload_size_mb` setting in `config.py`
3. Raises `ValidationException` with details for oversized files

---

### MEDIUM: Potential Path Traversal in S3 Keys - FIXED

**File:** `app/services/upload_service.py`
**Lines:** 47
**Status:** FIXED

**Issue:** The `file_name` is used directly in the S3 key without sanitization. A filename like `../../admin/secret.csv` could potentially write to unintended locations.

**Fix Applied:**
1. Added `_sanitize_filename()` method that:
   - Extracts only the base filename using `pathlib.Path.name`
   - Removes path separators, null bytes, and dangerous characters
   - Validates filename is not empty or just dots
   - Truncates overly long filenames while preserving extension

---

### MEDIUM: API Key in Memory

**File:** `app/services/llm_service.py`
**Lines:** 51, 59

```python
api_key = settings.anthropic_api_key.get_secret_value()
...
self._client = AsyncAnthropic(api_key=api_key)
```

**Issue:** The API key is extracted from SecretStr and stored in memory. While necessary for the SDK, the extracted value could appear in memory dumps or crash reports.

**Remediation Plan:**
1. This is a known limitation; ensure crash dumps are secured
2. Consider environment variable validation at startup
3. Document the security consideration in operational docs

---

### LOW: Missing CORS Configuration Documentation

**Issue:** No visible CORS configuration in the reviewed files. If CORS is configured elsewhere, ensure it's restrictive.

**Remediation Plan:**
1. Review `main.py` for CORS middleware configuration
2. Ensure allowed origins list is explicit, not wildcard
3. Document CORS policy in security documentation

---

## Spec/Design Review Notes

### Design Document: `2026-02-03-smart-upload-lob-aware-matching-design.md`

**Alignment:** The implementation aligns well with the design document. Key features implemented:
- LOB-to-NAICS mapping with curated + LLM fallback
- Industry-boosted role matching
- Grouped mappings by LOB in UI

**Gaps Identified:**
1. **Fuzzy matching**: Design mentions fuzzy matching but implementation notes pg_trgm dependency issue
2. **Caching strategy**: Design mentions caching LLM results, but no TTL or eviction policy visible
3. **Confidence boosting formula**: Implementation uses `INDUSTRY_BOOST_FACTOR = 0.25` but design doesn't specify the exact algorithm

---

## Recommendations Summary

### Immediate Actions (Critical/High)
1. Fix transaction corruption in `lob_mapping_repository.py` by adding rollback
2. Add file size limits to upload service
3. Sanitize filenames before use in S3 keys
4. Fix bare exception catches in S3 client
5. Add logging to S3 operations

### Short-term Improvements
1. Add input validation for LOB patterns and NAICS codes
2. Implement proper timeout handling for LLM calls
3. Add column existence validation in file parser
4. Improve logging consistency across services

### Long-term Considerations
1. Implement proper connection pooling for S3
2. Add distributed caching for LLM results with TTL
3. Consider streaming file parsing for large files
4. Add request tracing with correlation IDs

---

## Files Reviewed

| File | Status |
|------|--------|
| `app/services/lob_mapping_service.py` | Issues found |
| `app/repositories/lob_mapping_repository.py` | Critical issue |
| `app/services/s3_client.py` | High priority issues |
| `app/services/file_parser.py` | Medium priority issues |
| `app/services/llm_service.py` | Well-structured |
| `app/services/role_mapping_service.py` | Minor issues |
| `app/services/upload_service.py` | Security issues |
| `app/middleware/error_handler.py` | Well-structured |
| `app/exceptions.py` | Good exception hierarchy |
| `app/routers/lob_mappings.py` | Clean implementation |
| `tests/e2e/test_industry_mapping_flow.py` | Good coverage |

---

*Report generated by code-review skill*
