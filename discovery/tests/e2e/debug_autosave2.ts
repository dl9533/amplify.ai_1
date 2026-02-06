/**
 * Debug test to capture ALL console logs during upload.
 */
import { connect, waitForPageLoad } from "@/client.js";

const SERVER_URL = "http://localhost:9222";
const FRONTEND_URL = "http://localhost:5173";
const TEST_CSV = "/Users/dl9533/projects/amplify.ai_1/discovery/tests/e2e/test_data/tech_startup_workforce.csv";

async function runTest() {
  console.log("Debug test: Capturing ALL console logs...\n");

  const client = await connect(SERVER_URL);
  const page = await client.page("debug-test2", { viewport: { width: 1440, height: 900 } });

  // Capture ALL console logs from the browser
  page.on('console', msg => {
    console.log(`[BROWSER ${msg.type()}] ${msg.text()}`);
  });

  // Capture errors
  page.on('pageerror', error => {
    console.log(`[BROWSER ERROR] ${error.message}`);
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
    console.log("✅ File uploaded");

    // Wait for console logs
    await page.waitForTimeout(1000);

    // Select Role mapping
    console.log("\n🔧 Selecting Role mapping...");
    const selects = page.locator('select');
    for (let i = 0; i < await selects.count(); i++) {
      const select = selects.nth(i);
      const parentText = await select.locator('..').textContent();
      if (parentText?.includes('Job Title')) {
        await select.selectOption('role');
        console.log("   Selected Job Title -> Role");
        break;
      }
    }

    // Wait for auto-save
    console.log("\n⏳ Waiting for auto-save...");
    await page.waitForTimeout(2000);

    console.log("\nDone!");

  } catch (error) {
    console.error("❌ Error:", error);
  } finally {
    await client.disconnect();
  }
}

runTest().catch(console.error);
