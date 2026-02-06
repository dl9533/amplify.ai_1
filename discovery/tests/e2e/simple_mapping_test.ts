/**
 * Simple test that waits for mappings to be saved.
 */
import { connect, waitForPageLoad } from "@/client.js";

const SERVER_URL = "http://localhost:9222";
const FRONTEND_URL = "http://localhost:5173";
const API_URL = "http://localhost:8001";
const TEST_CSV = "/Users/dl9533/projects/amplify.ai_1/discovery/tests/e2e/test_data/tech_startup_workforce.csv";

async function runTest() {
  console.log("Simple mapping test...\n");

  const client = await connect(SERVER_URL);
  const page = await client.page("simple-test", { viewport: { width: 1440, height: 900 } });

  // Track errors
  page.on('pageerror', error => {
    console.log("[PAGE ERROR] " + error.message);
  });

  page.on('requestfailed', request => {
    console.log("[REQUEST FAILED] " + request.url() + " - " + request.failure()?.errorText);
  });

  try {
    // Login
    await page.goto(FRONTEND_URL);
    await waitForPageLoad(page);
    if (page.url().includes("/login")) {
      await page.fill('input[type="email"]', "test@example.com");
      await page.fill('input[type="password"]', "password123");
      await page.click('button:has-text("Sign in")');
      await page.waitForURL("**/discovery", { timeout: 10000 });
    }
    console.log("✅ Logged in");

    // Create session
    await page.locator('button:has-text("New Session"), button:has-text("Create First Session")').first().click();
    await page.waitForURL("**/upload", { timeout: 10000 });
    const sessionId = page.url().match(/discovery\/([a-f0-9-]+)\/upload/)?.[1] || "";
    console.log("✅ Session: " + sessionId);

    // Upload
    await page.locator('input[type="file"]').setInputFiles(TEST_CSV);
    await page.waitForSelector('text=rows detected', { timeout: 20000 });
    console.log("✅ Uploaded");

    // Get upload ID
    await page.waitForTimeout(500);
    const uploadsRes = await fetch(API_URL + "/discovery/sessions/" + sessionId + "/uploads");
    const uploads = await uploadsRes.json();
    const uploadId = uploads[0]?.id;
    console.log("   Upload ID: " + uploadId);

    // Check initial mappings
    console.log("   Initial column_mappings: " + JSON.stringify(uploads[0]?.column_mappings));

    // Select all mappings
    console.log("\n🔧 Selecting column mappings...");
    const selects = page.locator('select');
    const count = await selects.count();
    for (let i = 0; i < count; i++) {
      const select = selects.nth(i);
      const options = await select.locator('option').allTextContents();
      const parent = await select.locator('..').textContent();

      // Map based on column name
      if (parent?.includes('Job Title')) {
        await select.selectOption('role');
        console.log("   Job Title -> role");
      } else if (parent?.includes('Department') && !parent?.includes('LOB')) {
        await select.selectOption('department');
        console.log("   Department -> department");
      }
    }

    // Wait for debounced save (500ms) + extra buffer
    console.log("\n⏳ Waiting 3 seconds for auto-save...");
    await page.waitForTimeout(3000);

    // Check mappings again
    const uploadsRes2 = await fetch(API_URL + "/discovery/sessions/" + sessionId + "/uploads");
    const uploads2 = await uploadsRes2.json();
    console.log("\n📋 Final column_mappings: " + JSON.stringify(uploads2[0]?.column_mappings));

    if (uploads2[0]?.column_mappings?.role) {
      console.log("\n✅ SUCCESS: Auto-save worked!");
    } else {
      console.log("\n❌ FAILED: Mappings not saved");

      // Try clicking Continue to see if it triggers save
      console.log("\n🔄 Trying to click Continue...");
      const continueBtn = page.locator('button:has-text("Continue")');
      const isDisabled = await continueBtn.isDisabled();
      console.log("   Continue button disabled: " + isDisabled);

      if (!isDisabled) {
        await continueBtn.click();
        await page.waitForTimeout(2000);
        const uploadsRes3 = await fetch(API_URL + "/discovery/sessions/" + sessionId + "/uploads");
        const uploads3 = await uploadsRes3.json();
        console.log("   After Continue, column_mappings: " + JSON.stringify(uploads3[0]?.column_mappings));
      }
    }

  } catch (error) {
    console.error("❌ Error:", error);
  } finally {
    await client.disconnect();
  }
}

runTest().catch(console.error);
