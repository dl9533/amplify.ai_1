// tests/e2e/discovery/session-flow.spec.ts
import { test, expect } from '@playwright/test'

test.describe('Discovery Session Flow', () => {
  test('completes full 5-step discovery workflow', async ({ page }) => {
    // Step 1: Create new session and upload file
    await page.goto('/discovery')
    await page.click('button:has-text("New Discovery")')

    // Upload file
    const fileInput = page.locator('input[type="file"]')
    await fileInput.setInputFiles('tests/fixtures/sample-hr-data.csv')
    await expect(page.locator('text=data.csv')).toBeVisible()
    await page.click('button:has-text("Continue")')

    // Step 2: Map roles
    await expect(page.locator('text=Map your roles')).toBeVisible()
    await page.click('button:has-text("Confirm all above 80%")')
    await page.click('button:has-text("Continue")')

    // Step 3: Select activities
    await expect(page.locator('text=Select activities')).toBeVisible()
    await page.click('button:has-text("Select high exposure")')
    await page.click('button:has-text("Continue")')

    // Step 4: Review analysis
    await expect(page.locator('text=Analysis')).toBeVisible()
    await expect(page.locator('[data-testid="analysis-result-card"]').first()).toBeVisible()
    await page.click('button:has-text("Continue")')

    // Step 5: Build roadmap and handoff
    await expect(page.locator('text=Roadmap')).toBeVisible()
    await expect(page.locator('[data-testid="column-NOW"]')).toBeVisible()
    await page.click('button:has-text("Send to Intake")')
    await page.click('button:has-text("Confirm")')

    // Verify handoff complete
    await expect(page.locator('text=Successfully submitted')).toBeVisible()
  })

  test('saves progress between steps', async ({ page }) => {
    await page.goto('/discovery/test-session/map-roles')
    await page.click('button:has-text("Confirm"):first')

    // Navigate away and back
    await page.goto('/discovery')
    await page.click('a:has-text("Continue")')

    // Verify progress preserved
    await expect(page.locator('[data-testid="confirmed-badge"]')).toBeVisible()
  })

  test('chat panel provides contextual help', async ({ page }) => {
    await page.goto('/discovery/test-session/activities')

    // Send message
    await page.fill('[aria-label="Message"]', 'What activities should I select?')
    await page.click('button:has-text("Send")')

    // Verify response
    await expect(page.locator('text=high AI exposure')).toBeVisible({ timeout: 10000 })
  })
})
