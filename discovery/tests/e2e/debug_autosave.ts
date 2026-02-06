/**
 * Debug test to capture console logs during upload and mapping flow.
 */
import { connect, waitForPageLoad } from "@/client.js";

const SERVER_URL = "http://localhost:9222";
const FRONTEND_URL = "http://localhost:5173";
const TEST_CSV = "/Users/dl9533/projects/amplify.ai_1/discovery/tests/e2e/test_data/tech_startup_workforce.csv";

async function runTest() {
  console.log("Debug test: Capturing console logs during upload flow...\n");

  const client = await connect(SERVER_URL);
  const page = await client.page("debug-test", { viewport: { width: 1440, height: 900 } });

  // Capture console logs from the browser
  page.on('console', msg => {
    const text = msg.text();
    if (text.includes('useFileUpload') || text.includes('UploadStep') || text.includes('Auto-save')) {
      console.log(`[BROWSER] ${text}`);
    }
  });

  try {
    // Navigate and login
    await page.goto(FRONTEND_URL);
    await waitForPageLoad(page);

    const currentUrl = page.url();
    if (currentUrl.includes("/login")) {
      await page.fill('input[type="email"]', "test@example.com");
      await page.fill('input[type="password"]', "password123");
      await page.click('button:has-text("Sign in")');
      await page.waitForURL("**/discovery", { timeout: 10000 });
    }
    console.log("✅ Logged in");

    // Create new session
    const newSessionBtn = page.locator('button:has-text("New Session"), button:has-text("Create First Session")').first();
    await newSessionBtn.click();
    await page.waitForURL("**/upload", { timeout: 10000 });
    await waitForPageLoad(page);
    console.log("✅ Created session");

    // Upload file
    console.log("\n📤 Uploading file...");
    const fileInput = page.locator('input[type="file"]');
    await fileInput.setInputFiles(TEST_CSV);
    await page.waitForSelector('text=rows detected', { timeout: 20000 });
    console.log("✅ File uploaded - waiting for console output...");

    // Wait a bit for all console logs to come through
    await page.waitForTimeout(2000);

    // Select Role mapping manually
    console.log("\n🔧 Selecting Role mapping...");
    const selects = page.locator('select');
    const selectCount = await selects.count();
    console.log("   Found " + selectCount + " selects");

    for (let i = 0; i < selectCount; i++) {
      const select = selects.nth(i);
      const parentText = await select.locator('..').textContent();
      if (parentText?.includes('Job Title')) {
        console.log("   Found Job Title select, selecting 'role'");
        await select.selectOption('role');
        break;
      }
    }

    // Wait for auto-save to trigger
    console.log("\n⏳ Waiting for auto-save (2 seconds)...");
    await page.waitForTimeout(2000);

    console.log("\n📋 Test complete - check BROWSER logs above for debug info");

  } catch (error) {
    console.error("\n❌ Test failed:", error);
  } finally {
    await client.disconnect();
  }
}

runTest().catch(console.error);
