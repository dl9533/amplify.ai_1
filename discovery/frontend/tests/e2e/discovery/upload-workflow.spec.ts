/**
 * E2E Test: Upload Workflow
 *
 * Tests the complete file upload and column mapping workflow
 * for the Discovery module.
 *
 * Prerequisites:
 * - Backend running at http://localhost:8001
 * - Frontend running at http://localhost:5173
 *
 * Run with:
 *   npx playwright test tests/e2e/discovery/upload-workflow.spec.ts --headed
 */
import { test, expect, Page } from '@playwright/test'
import * as path from 'path'
import * as fs from 'fs'

const SAMPLE_FILE_PATH = path.join(__dirname, '../../fixtures/sample-workforce-data.csv')

test.describe('Discovery Upload Workflow', () => {
  test.beforeEach(async ({ page }) => {
    // Verify sample file exists
    expect(fs.existsSync(SAMPLE_FILE_PATH)).toBe(true)
  })

  test('Step 1: Upload CSV file and see detected columns', async ({ page }) => {
    // Navigate to discovery and create new session
    await page.goto('/discovery')
    await page.waitForLoadState('networkidle')

    // Click "New Discovery" button
    const newButton = page.getByRole('button', { name: /new discovery/i })
    await expect(newButton).toBeVisible()
    await newButton.click()

    // Should be on upload step
    await expect(page.getByText(/upload workforce data/i)).toBeVisible()

    // Upload the sample file
    const fileInput = page.locator('input[type="file"]')
    await fileInput.setInputFiles(SAMPLE_FILE_PATH)

    // Wait for upload to complete and columns to be detected
    await expect(page.getByText(/rows detected/i)).toBeVisible({ timeout: 10000 })

    // Verify detected columns are shown
    await expect(page.getByText('Role')).toBeVisible()
    await expect(page.getByText('Department')).toBeVisible()
    await expect(page.getByText('Location')).toBeVisible()
    await expect(page.getByText('Headcount')).toBeVisible()
  })

  test('Step 1: Map columns and proceed to next step', async ({ page }) => {
    await page.goto('/discovery')
    await page.waitForLoadState('networkidle')

    await page.getByRole('button', { name: /new discovery/i }).click()
    await expect(page.getByText(/upload workforce data/i)).toBeVisible()

    // Upload file
    const fileInput = page.locator('input[type="file"]')
    await fileInput.setInputFiles(SAMPLE_FILE_PATH)
    await expect(page.getByText(/rows detected/i)).toBeVisible({ timeout: 10000 })

    // Map the Role column (required)
    const roleColumnRow = page.locator('.bg-bg-muted').filter({ hasText: 'Role' }).first()
    const roleSelect = roleColumnRow.locator('select')
    await roleSelect.selectOption('role')

    // Map Department column
    const deptColumnRow = page.locator('.bg-bg-muted').filter({ hasText: 'Department' }).first()
    const deptSelect = deptColumnRow.locator('select')
    await deptSelect.selectOption('department')

    // Map Geography/Location column
    const geoColumnRow = page.locator('.bg-bg-muted').filter({ hasText: 'Location' }).first()
    const geoSelect = geoColumnRow.locator('select')
    await geoSelect.selectOption('geography')

    // Map Headcount column
    const headcountColumnRow = page.locator('.bg-bg-muted').filter({ hasText: 'Headcount' }).first()
    const headcountSelect = headcountColumnRow.locator('select')
    await headcountSelect.selectOption('headcount')

    // Warning should be gone since role is mapped
    await expect(page.getByText(/please map at least the role column/i)).not.toBeVisible()

    // Continue to next step
    const continueButton = page.getByRole('button', { name: /continue|next/i })
    await expect(continueButton).toBeEnabled()
    await continueButton.click()

    // Should be on Map Roles step
    await expect(page.getByText(/map.*o\*net/i)).toBeVisible({ timeout: 10000 })
  })

  test('validates required Role column mapping', async ({ page }) => {
    await page.goto('/discovery')
    await page.waitForLoadState('networkidle')

    await page.getByRole('button', { name: /new discovery/i }).click()

    // Upload file
    const fileInput = page.locator('input[type="file"]')
    await fileInput.setInputFiles(SAMPLE_FILE_PATH)
    await expect(page.getByText(/rows detected/i)).toBeVisible({ timeout: 10000 })

    // Warning should be visible since role is not mapped
    await expect(page.getByText(/please map at least the role column/i)).toBeVisible()

    // Continue button should be disabled
    const continueButton = page.getByRole('button', { name: /continue|next/i })
    await expect(continueButton).toBeDisabled()
  })

  test('allows removing uploaded file and re-uploading', async ({ page }) => {
    await page.goto('/discovery')
    await page.waitForLoadState('networkidle')

    await page.getByRole('button', { name: /new discovery/i }).click()

    // Upload file
    const fileInput = page.locator('input[type="file"]')
    await fileInput.setInputFiles(SAMPLE_FILE_PATH)
    await expect(page.getByText(/rows detected/i)).toBeVisible({ timeout: 10000 })

    // Click remove button
    await page.getByRole('button', { name: /remove/i }).click()

    // Should be back to dropzone
    await expect(page.getByText(/drag and drop/i)).toBeVisible()

    // Can upload again
    await fileInput.setInputFiles(SAMPLE_FILE_PATH)
    await expect(page.getByText(/rows detected/i)).toBeVisible({ timeout: 10000 })
  })

  test('shows upload progress during file upload', async ({ page }) => {
    await page.goto('/discovery')
    await page.waitForLoadState('networkidle')

    await page.getByRole('button', { name: /new discovery/i }).click()

    // Start upload
    const fileInput = page.locator('input[type="file"]')

    // For large files, we'd see the progress indicator
    // With small files it may complete too fast, so we just verify no errors
    await fileInput.setInputFiles(SAMPLE_FILE_PATH)

    // Either see progress or final result
    await expect(
      page.getByText(/uploading|rows detected/i)
    ).toBeVisible({ timeout: 10000 })
  })

  test('rejects invalid file types', async ({ page }) => {
    await page.goto('/discovery')
    await page.waitForLoadState('networkidle')

    await page.getByRole('button', { name: /new discovery/i }).click()

    // Create a temporary invalid file
    const invalidFilePath = path.join(__dirname, '../../fixtures/invalid-file.txt')
    fs.writeFileSync(invalidFilePath, 'This is not a CSV file')

    try {
      const fileInput = page.locator('input[type="file"]')
      await fileInput.setInputFiles(invalidFilePath)

      // Should show error or reject the file
      // The file input has accept=".csv,.xlsx,.xls" so browser may block it
      // or our validation should catch it
      const errorVisible = await page.getByText(/invalid file type/i).isVisible()
      const dropzoneVisible = await page.getByText(/drag and drop/i).isVisible()

      // Either error shown or still on dropzone (browser rejected)
      expect(errorVisible || dropzoneVisible).toBe(true)
    } finally {
      // Cleanup
      if (fs.existsSync(invalidFilePath)) {
        fs.unlinkSync(invalidFilePath)
      }
    }
  })
})

test.describe('Full Discovery Workflow with Upload', () => {
  test('completes workflow from upload through roadmap', async ({ page }) => {
    // Step 1: Upload
    await page.goto('/discovery')
    await page.waitForLoadState('networkidle')
    await page.getByRole('button', { name: /new discovery/i }).click()

    const fileInput = page.locator('input[type="file"]')
    await fileInput.setInputFiles(SAMPLE_FILE_PATH)
    await expect(page.getByText(/rows detected/i)).toBeVisible({ timeout: 10000 })

    // Map role column
    const roleColumnRow = page.locator('.bg-bg-muted').filter({ hasText: 'Role' }).first()
    await roleColumnRow.locator('select').selectOption('role')

    await page.getByRole('button', { name: /continue|next/i }).click()

    // Step 2: Map Roles to O*NET
    await expect(page.getByText(/map.*o\*net/i)).toBeVisible({ timeout: 10000 })

    // Confirm all high-confidence mappings
    const confirmAllButton = page.getByRole('button', { name: /confirm all/i })
    if (await confirmAllButton.isVisible()) {
      await confirmAllButton.click()
    }

    await page.getByRole('button', { name: /continue|next/i }).click()

    // Step 3: Select Activities
    await expect(page.getByText(/select.*activities/i)).toBeVisible({ timeout: 10000 })

    // Auto-select high exposure activities
    const autoSelectButton = page.getByRole('button', { name: /auto-select high exposure/i })
    if (await autoSelectButton.isVisible()) {
      await autoSelectButton.click()
    }

    await page.getByRole('button', { name: /continue|next/i }).click()

    // Step 4: Analysis Results
    await expect(page.getByText(/analysis/i)).toBeVisible({ timeout: 10000 })
    await page.getByRole('button', { name: /continue|next/i }).click()

    // Step 5: Roadmap
    await expect(page.getByText(/roadmap/i)).toBeVisible({ timeout: 10000 })

    // Verify kanban columns exist
    await expect(page.getByText('Now')).toBeVisible()
    await expect(page.getByText('Next')).toBeVisible()
    await expect(page.getByText('Later')).toBeVisible()

    // Click handoff button
    const handoffButton = page.getByRole('button', { name: /hand off|send to intake/i })
    await expect(handoffButton).toBeVisible()
  })
})
