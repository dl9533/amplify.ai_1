# Test Fixtures

## Sample Workforce Data

The file `sample-workforce-data.csv` contains sample workforce data for testing the Discovery workflow.

### File Contents (20 rows)

| Role | Department | Location | Headcount |
|------|------------|----------|-----------|
| Software Engineer | Engineering | San Francisco | 45 |
| Data Analyst | Analytics | New York | 22 |
| Customer Support Representative | Support | Austin | 67 |
| Product Manager | Product | San Francisco | 12 |
| Financial Analyst | Finance | New York | 18 |
| ... | ... | ... | ... |

### Columns

- **Role**: Job title (required for O*NET mapping)
- **Department**: Business unit
- **Location**: Office location or "Remote"
- **Headcount**: Number of employees in that role

### Usage

1. Upload via the Discovery UI at Step 1
2. Map columns:
   - Role → role (required)
   - Department → department
   - Location → geography
   - Headcount → headcount

3. Proceed through the workflow
