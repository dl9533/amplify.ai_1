"""O*NET file-based database sync service.

Downloads and imports the full O*NET database from official release files.
This provides complete coverage of ~923 occupations, alternate titles, and tasks.
"""
import csv
import io
import logging
import uuid
import zipfile
from dataclasses import dataclass
from typing import Any

import httpx

from app.repositories.onet_repository import OnetRepository

logger = logging.getLogger(__name__)


class OnetSyncError(Exception):
    """Base exception for O*NET sync errors."""

    pass


class OnetDownloadError(OnetSyncError):
    """Error downloading O*NET database files."""

    pass


class OnetParseError(OnetSyncError):
    """Error parsing O*NET data files."""

    pass


@dataclass
class SyncResult:
    """Result of an O*NET sync operation."""

    version: str
    occupation_count: int
    alternate_title_count: int
    task_count: int
    industry_count: int
    gwa_count: int
    iwa_count: int
    dwa_count: int
    task_to_dwa_count: int
    status: str


class OnetFileSyncService:
    """Service for downloading and importing O*NET database.

    Downloads O*NET database releases from the O*NET Resource Center
    and imports occupation data, alternate titles, and tasks into
    the local database.

    This provides complete O*NET coverage unlike API-based sync which
    is limited by search results.

    Transaction Management:
    - The sync() method manages transactions, committing on success
      or rolling back on failure to ensure data integrity.
    """

    ONET_BASE_URL = "https://www.onetcenter.org/dl_files/database"

    # File names in the O*NET zip
    OCCUPATION_FILE = "Occupation Data.txt"
    ALTERNATE_TITLES_FILE = "Alternate Titles.txt"
    TASKS_FILE = "Task Statements.txt"
    INDUSTRY_FILE = "Industry.txt"
    CONTENT_MODEL_FILE = "Content Model Reference.txt"
    DWA_REFERENCE_FILE = "DWA Reference.txt"
    TASKS_TO_DWAS_FILE = "Tasks to DWAs.txt"

    def __init__(self, repository: OnetRepository) -> None:
        """Initialize sync service.

        Args:
            repository: OnetRepository for database operations.
        """
        self.repository = repository

    async def sync(self, version: str = "30_1") -> SyncResult:
        """Download and import O*NET data.

        This method manages the entire sync transaction:
        - Downloads the O*NET database zip file
        - Parses occupation, alternate title, and task data
        - Upserts all data to the database
        - Commits on success, rolls back on any failure

        Args:
            version: O*NET version to download (e.g., "30_1" for v30.1).

        Returns:
            SyncResult with counts and status.

        Raises:
            OnetDownloadError: If download fails.
            OnetParseError: If parsing fails.
            OnetSyncError: For other sync failures.
        """
        display_version = version.replace("_", ".")
        logger.info(f"Starting O*NET sync for version {display_version}")

        try:
            # Download zip file
            try:
                zip_data = await self._download(version)
            except httpx.HTTPError as e:
                logger.error(f"Download failed: {e}")
                raise OnetDownloadError(f"Failed to download O*NET {display_version}") from e

            # Extract and parse files
            try:
                occupations, alt_titles, tasks, industries, gwas, iwas, dwas, tasks_to_dwas = self._extract_and_parse(zip_data)
            except (zipfile.BadZipFile, KeyError) as e:
                logger.error(f"Parse failed: {e}")
                raise OnetParseError(f"Invalid O*NET archive for version {display_version}") from e

            # Upsert to database (within implicit transaction)
            logger.info(
                f"Importing {len(occupations)} occupations, {len(alt_titles)} alternate titles, "
                f"{len(tasks)} tasks, {len(industries)} industries, "
                f"{len(gwas)} GWAs, {len(iwas)} IWAs, {len(dwas)} DWAs, "
                f"{len(tasks_to_dwas)} task-to-DWA mappings"
            )

            occ_count = await self.repository.bulk_upsert_occupations(occupations)
            alt_count = await self.repository.bulk_replace_alternate_titles(alt_titles)
            task_count = await self.repository.bulk_replace_tasks(tasks)
            ind_count = await self.repository.bulk_upsert_industries(industries)

            # Sync work activities (GWAs must come first, then IWAs, then DWAs due to FK constraints)
            gwa_count = await self.repository.bulk_upsert_gwas(gwas)
            iwa_count = await self.repository.bulk_upsert_iwas(iwas)
            dwa_count = await self.repository.bulk_upsert_dwas(dwas)

            # Sync task-to-DWA mappings (must come after tasks and DWAs)
            task_to_dwa_count = await self._sync_task_to_dwa_mappings(tasks_to_dwas)

            # Log sync success
            await self.repository.log_sync(
                version=display_version,
                occupation_count=occ_count,
                alternate_title_count=alt_count,
                task_count=task_count,
                status="success",
            )

            # Commit the transaction
            await self.repository.session.commit()

            logger.info(
                f"O*NET sync complete: {occ_count} occupations, "
                f"{alt_count} alternate titles, {task_count} tasks, {ind_count} industries, "
                f"{gwa_count} GWAs, {iwa_count} IWAs, {dwa_count} DWAs, "
                f"{task_to_dwa_count} task-to-DWA mappings"
            )

            return SyncResult(
                version=display_version,
                occupation_count=occ_count,
                alternate_title_count=alt_count,
                task_count=task_count,
                industry_count=ind_count,
                gwa_count=gwa_count,
                iwa_count=iwa_count,
                dwa_count=dwa_count,
                task_to_dwa_count=task_to_dwa_count,
                status="success",
            )

        except OnetSyncError:
            # Re-raise known sync errors after logging failure
            await self._log_failure(display_version)
            raise

        except Exception as e:
            # Handle unexpected errors
            logger.error(f"Unexpected sync error: {e}", exc_info=True)
            await self._log_failure(display_version)
            raise OnetSyncError(f"Sync failed unexpectedly: {e}") from e

    async def _sync_task_to_dwa_mappings(
        self,
        tasks_to_dwas: list[dict[str, Any]],
    ) -> int:
        """Sync task-to-DWA mappings to database.

        This correlates O*NET Task IDs with our internal task IDs
        and creates the junction table entries.

        Args:
            tasks_to_dwas: List of parsed task-to-DWA mappings with
                occupation_code, onet_task_id, and dwa_id.

        Returns:
            Number of mappings created.
        """
        if not tasks_to_dwas:
            logger.info("No task-to-DWA mappings to sync")
            return 0

        # Get mapping from (occupation_code, onet_task_id) -> internal task_id
        task_id_mapping = await self.repository.get_task_id_mapping()

        if not task_id_mapping:
            logger.warning("No tasks with onet_task_id found - cannot create task-to-DWA mappings")
            return 0

        # Convert to internal task IDs
        mappings_to_insert = []
        skipped = 0

        for mapping in tasks_to_dwas:
            key = (mapping["occupation_code"], mapping["onet_task_id"])
            internal_task_id = task_id_mapping.get(key)

            if internal_task_id is None:
                skipped += 1
                continue

            mappings_to_insert.append({
                "task_id": internal_task_id,
                "dwa_id": mapping["dwa_id"],
            })

        if skipped > 0:
            skipped_pct = (skipped / len(tasks_to_dwas)) * 100
            logger.warning(
                f"Skipped {skipped}/{len(tasks_to_dwas)} ({skipped_pct:.1f}%) "
                f"task-to-DWA mappings (task not found)"
            )

            # Fail sync if more than 50% of mappings couldn't be resolved
            # This indicates a data quality issue that needs investigation
            if skipped_pct > 50:
                raise OnetSyncError(
                    f"Too many task-to-DWA mappings failed ({skipped}/{len(tasks_to_dwas)}, "
                    f"{skipped_pct:.1f}%). Check Task ID consistency between files."
                )

        # Bulk insert
        count = await self.repository.bulk_replace_task_to_dwa_mappings(mappings_to_insert)
        logger.info(f"Created {count} task-to-DWA mappings")
        return count

    async def _log_failure(self, version: str) -> None:
        """Log a failed sync attempt and rollback.

        Args:
            version: O*NET version that failed.
        """
        try:
            # Rollback any partial changes
            await self.repository.session.rollback()

            # Log the failure (in a new transaction)
            await self.repository.log_sync(
                version=version,
                occupation_count=0,
                alternate_title_count=0,
                task_count=0,
                status="failed",
            )
            await self.repository.session.commit()
        except Exception as log_error:
            logger.error(f"Failed to log sync failure: {log_error}")

    async def _download(self, version: str) -> bytes:
        """Download O*NET database zip file.

        Args:
            version: O*NET version (e.g., "30_1").

        Returns:
            Zip file contents as bytes.

        Raises:
            httpx.HTTPError: On download failure.
        """
        url = f"{self.ONET_BASE_URL}/db_{version}_text.zip"

        async with httpx.AsyncClient(timeout=300.0) as client:
            logger.info(f"Downloading O*NET from {url}")
            response = await client.get(url)
            response.raise_for_status()
            return response.content

    def _extract_and_parse(
        self,
        zip_data: bytes,
    ) -> tuple[list[dict], list[dict], list[dict], list[dict], list[dict], list[dict], list[dict], list[dict]]:
        """Extract and parse O*NET data files from zip.

        Args:
            zip_data: Zip file contents.

        Returns:
            Tuple of (occupations, alternate_titles, tasks, industries, gwas, iwas, dwas, tasks_to_dwas).

        Raises:
            zipfile.BadZipFile: If zip is invalid.
            KeyError: If expected files are missing.
        """
        with zipfile.ZipFile(io.BytesIO(zip_data)) as zf:
            # Find the directory prefix (e.g., "db_30_1_text/")
            names = zf.namelist()
            prefix = names[0].split("/")[0] + "/" if "/" in names[0] else ""

            # Read and parse each file
            occ_content = zf.read(f"{prefix}{self.OCCUPATION_FILE}").decode("utf-8")
            alt_content = zf.read(f"{prefix}{self.ALTERNATE_TITLES_FILE}").decode("utf-8")
            task_content = zf.read(f"{prefix}{self.TASKS_FILE}").decode("utf-8")

            # Try to read industry file (may not exist in all versions)
            try:
                ind_content = zf.read(f"{prefix}{self.INDUSTRY_FILE}").decode("utf-8")
            except KeyError:
                ind_content = ""

            # Read work activities files
            content_model = zf.read(f"{prefix}{self.CONTENT_MODEL_FILE}").decode("utf-8")
            dwa_reference = zf.read(f"{prefix}{self.DWA_REFERENCE_FILE}").decode("utf-8")

            # Read Tasks to DWAs mapping file
            try:
                tasks_to_dwas_content = zf.read(f"{prefix}{self.TASKS_TO_DWAS_FILE}").decode("utf-8")
            except KeyError:
                logger.warning(f"Tasks to DWAs file not found in O*NET archive")
                tasks_to_dwas_content = ""

        occupations = self._parse_occupations(occ_content)
        alt_titles = self._parse_alternate_titles(alt_content)
        tasks = self._parse_tasks(task_content)
        industries = self._parse_industries(ind_content) if ind_content else []

        # Parse work activities
        gwas = self._parse_gwas(content_model)
        iwas, dwas = self._parse_dwa_reference(dwa_reference)

        # Parse Tasks to DWAs mapping
        tasks_to_dwas = self._parse_tasks_to_dwas(tasks_to_dwas_content) if tasks_to_dwas_content else []

        return occupations, alt_titles, tasks, industries, gwas, iwas, dwas, tasks_to_dwas

    def _parse_occupations(self, content: str) -> list[dict[str, Any]]:
        """Parse occupation data from tab-separated content.

        Args:
            content: Tab-separated occupation data.

        Returns:
            List of occupation dicts.
        """
        reader = csv.DictReader(io.StringIO(content), delimiter="\t")
        occupations = []

        for row in reader:
            occupations.append({
                "code": row["O*NET-SOC Code"],
                "title": row["Title"],
                "description": row.get("Description", ""),
            })

        return occupations

    def _parse_alternate_titles(self, content: str) -> list[dict[str, Any]]:
        """Parse alternate titles from tab-separated content.

        Args:
            content: Tab-separated alternate titles data.

        Returns:
            List of alternate title dicts.
        """
        reader = csv.DictReader(io.StringIO(content), delimiter="\t")
        titles = []

        for row in reader:
            titles.append({
                "id": uuid.uuid4(),
                "onet_code": row["O*NET-SOC Code"],
                "title": row["Alternate Title"],
            })

        return titles

    def _parse_tasks(self, content: str) -> list[dict[str, Any]]:
        """Parse task statements from tab-separated content.

        The Task Statements file contains columns:
        - O*NET-SOC Code
        - Task ID (unique identifier within O*NET)
        - Task (description)
        - Task Type (optional)
        - Incumbents Responding (optional)
        - Date
        - Domain Source

        Args:
            content: Tab-separated task data.

        Returns:
            List of task dicts with occupation_code, onet_task_id, description.
        """
        reader = csv.DictReader(io.StringIO(content), delimiter="\t")
        tasks = []
        missing_task_id_count = 0

        for row in reader:
            # Parse the O*NET Task ID (integer identifier)
            onet_task_id = None
            if row.get("Task ID"):
                try:
                    onet_task_id = int(row["Task ID"])
                except (ValueError, TypeError):
                    missing_task_id_count += 1
            else:
                missing_task_id_count += 1

            tasks.append({
                "occupation_code": row["O*NET-SOC Code"],
                "onet_task_id": onet_task_id,
                "description": row["Task"],
                "importance": None,  # Not available in Task Statements file
            })

        logger.info(f"Parsed {len(tasks)} tasks from Task Statements")
        if missing_task_id_count > 0:
            pct = (missing_task_id_count / len(tasks)) * 100 if tasks else 0
            logger.warning(
                f"{missing_task_id_count}/{len(tasks)} tasks ({pct:.1f}%) "
                f"missing Task ID - cannot link to DWAs"
            )
        return tasks

    def _parse_industries(self, content: str) -> list[dict[str, Any]]:
        """Parse industry data from tab-separated content.

        Args:
            content: Tab-separated industry data.

        Returns:
            List of industry dicts.
        """
        if not content or not content.strip():
            return []

        reader = csv.DictReader(io.StringIO(content), delimiter="\t")
        industries = []

        for row in reader:
            employment = None
            if row.get("Employment"):
                try:
                    employment = float(row["Employment"])
                except (ValueError, TypeError):
                    pass

            industries.append({
                "occupation_code": row["O*NET-SOC Code"],
                "naics_code": row["Industry Code"],
                "naics_title": row["Industry Title"],
                "employment_percent": employment,
            })

        return industries

    def _parse_gwas(self, content: str) -> list[dict[str, Any]]:
        """Parse GWAs from Content Model Reference.

        GWAs are identified by Element IDs starting with '4.A.' that have
        exactly 5 parts (e.g., '4.A.1.a.1' for 'Getting Information').

        Args:
            content: Tab-separated Content Model Reference data.

        Returns:
            List of GWA dicts with id, name, description.
        """
        reader = csv.DictReader(io.StringIO(content), delimiter="\t")
        gwas = []
        seen_ids = set()

        for row in reader:
            element_id = row.get("Element ID", "")
            # GWAs start with 4.A. and have format like 4.A.1.a.1 (5 parts)
            if element_id.startswith("4.A.") and element_id not in seen_ids:
                parts = element_id.split(".")
                # GWAs have exactly 5 parts (like 4.A.1.a.1)
                if len(parts) == 5:
                    seen_ids.add(element_id)
                    gwas.append({
                        "id": element_id,
                        "name": row.get("Element Name", ""),
                        "description": row.get("Description", ""),
                        "ai_exposure_score": None,  # Set later from Pew research data
                    })

        logger.info(f"Parsed {len(gwas)} GWAs from Content Model Reference")
        return gwas

    def _parse_dwa_reference(self, content: str) -> tuple[list[dict[str, Any]], list[dict[str, Any]]]:
        """Parse IWAs and DWAs from DWA Reference file.

        The DWA Reference file contains Element ID (GWA), IWA ID, DWA ID, and DWA Title.
        We extract unique IWAs and all DWAs from this file.

        Args:
            content: Tab-separated DWA Reference data.

        Returns:
            Tuple of (iwas, dwas) lists.
        """
        reader = csv.DictReader(io.StringIO(content), delimiter="\t")
        iwas = []
        dwas = []
        seen_iwa_ids = set()

        for row in reader:
            gwa_id = row.get("Element ID", "")
            iwa_id = row.get("IWA ID", "")
            dwa_id = row.get("DWA ID", "")
            dwa_title = row.get("DWA Title", "")

            # Skip invalid rows
            if not gwa_id or not iwa_id or not dwa_id:
                continue

            # Extract unique IWAs
            if iwa_id not in seen_iwa_ids:
                seen_iwa_ids.add(iwa_id)
                iwas.append({
                    "id": iwa_id,
                    "gwa_id": gwa_id,
                    "name": f"IWA: {iwa_id}",  # IWAs don't have names in this file
                    "description": None,
                })

            # Add DWA
            dwas.append({
                "id": dwa_id,
                "iwa_id": iwa_id,
                "name": dwa_title,
                "description": None,
            })

        logger.info(f"Parsed {len(iwas)} IWAs and {len(dwas)} DWAs from DWA Reference")
        return iwas, dwas

    def _parse_tasks_to_dwas(self, content: str) -> list[dict[str, Any]]:
        """Parse Tasks to DWAs mapping from tab-separated content.

        The Tasks to DWAs file contains columns:
        - O*NET-SOC Code
        - Title (occupation title)
        - Task ID
        - Task (description)
        - DWA ID
        - DWA Title
        - Date
        - Domain Source

        This maps O*NET Task IDs to DWA IDs for correlation.

        Args:
            content: Tab-separated Tasks to DWAs data.

        Returns:
            List of dicts with occupation_code, onet_task_id, dwa_id.
        """
        if not content or not content.strip():
            return []

        reader = csv.DictReader(io.StringIO(content), delimiter="\t")
        mappings = []
        seen = set()  # Track unique (occupation_code, task_id, dwa_id) tuples

        for row in reader:
            occupation_code = row.get("O*NET-SOC Code", "")
            task_id_str = row.get("Task ID", "")
            dwa_id = row.get("DWA ID", "")

            # Skip invalid rows
            if not occupation_code or not task_id_str or not dwa_id:
                continue

            # Parse task ID as integer
            try:
                onet_task_id = int(task_id_str)
            except (ValueError, TypeError):
                continue

            # Skip duplicates
            key = (occupation_code, onet_task_id, dwa_id)
            if key in seen:
                continue
            seen.add(key)

            mappings.append({
                "occupation_code": occupation_code,
                "onet_task_id": onet_task_id,
                "dwa_id": dwa_id,
            })

        logger.info(f"Parsed {len(mappings)} Task-to-DWA mappings")
        return mappings

    async def get_sync_status(self) -> dict[str, Any]:
        """Get current sync status.

        Returns:
            Dict with sync status information.
        """
        latest = await self.repository.get_latest_sync()
        count = await self.repository.count()

        return {
            "synced": latest is not None,
            "version": latest.version if latest else None,
            "synced_at": latest.synced_at.isoformat() if latest else None,
            "occupation_count": count,
        }
