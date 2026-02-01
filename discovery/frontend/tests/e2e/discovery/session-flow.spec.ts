// tests/e2e/discovery/session-flow.spec.ts
import { test, expect } from '@playwright/test'
import * as path from 'path'

/** Timeout for chat response expectations */
const CHAT_RESPONSE_TIMEOUT = 10000

test.describe('Discovery Session Flow', () => {
  test('completes full 5-step discovery workflow', async ({ page }) => {
    // Step 1: Create new session and upload file
    await page.goto('/discovery')
    await page.waitForLoadState('networkidle')
    await page.getByRole('button', { name: 'New Discovery' }).click()

    // Upload file
    const fileInput = page.locator('input[type="file"]')
    await fileInput.setInputFiles(path.join(__dirname, '../../fixtures/sample-hr-data.csv'))
    await expect(page.locator('text=data.csv')).toBeVisible()
    await page.getByRole('button', { name: 'Continue' }).click()

    // Step 2: Map roles
    await page.waitForLoadState('networkidle')
    await expect(page.locator('text=Map your roles')).toBeVisible()
    await page.getByRole('button', { name: 'Confirm all above 80%' }).click()
    await page.getByRole('button', { name: 'Continue' }).click()

    // Step 3: Select activities
    await page.waitForLoadState('networkidle')
    await expect(page.locator('text=Select activities')).toBeVisible()
    await page.getByRole('button', { name: 'Select high exposure' }).click()
    await page.getByRole('button', { name: 'Continue' }).click()

    // Step 4: Review analysis
    await page.waitForLoadState('networkidle')
    await expect(page.locator('text=Analysis')).toBeVisible()
    await expect(page.locator('[data-testid="analysis-result-card"]').first()).toBeVisible()
    await page.getByRole('button', { name: 'Continue' }).click()

    // Step 5: Build roadmap and handoff
    await page.waitForLoadState('networkidle')
    await expect(page.locator('text=Roadmap')).toBeVisible()
    await expect(page.locator('[data-testid="column-NOW"]')).toBeVisible()
    await page.getByRole('button', { name: 'Send to Intake' }).click()
    await page.getByRole('button', { name: 'Confirm' }).click()

    // Verify handoff complete
    await expect(page.locator('text=Successfully submitted')).toBeVisible()
  })

  test('saves progress between steps', async ({ page }) => {
    await page.goto('/discovery/test-session/map-roles')
    await page.waitForLoadState('networkidle')
    await page.getByRole('button', { name: 'Confirm' }).first().click()

    // Navigate away and back
    await page.goto('/discovery')
    await page.waitForLoadState('networkidle')
    await page.getByRole('link', { name: 'Continue' }).click()

    // Verify progress preserved
    await expect(page.locator('[data-testid="confirmed-badge"]')).toBeVisible()
  })

  test('chat panel provides contextual help', async ({ page }) => {
    await page.goto('/discovery/test-session/activities')
    await page.waitForLoadState('networkidle')

    // Send message
    await page.getByLabel('Message').fill('What activities should I select?')
    await page.getByRole('button', { name: 'Send' }).click()

    // Verify response
    await expect(page.locator('text=high AI exposure')).toBeVisible({ timeout: CHAT_RESPONSE_TIMEOUT })
  })
})
