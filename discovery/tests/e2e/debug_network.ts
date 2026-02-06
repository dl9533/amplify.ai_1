/**
 * Debug test to capture network requests during upload flow.
 */
import { connect, waitForPageLoad } from "@/client.js";

const SERVER_URL = "http://localhost:9222";
const FRONTEND_URL = "http://localhost:5173";
const API_URL = "http://localhost:8001";
const TEST_CSV = "/Users/dl9533/projects/amplify.ai_1/discovery/tests/e2e/test_data/tech_startup_workforce.csv";

async function runTest() {
  console.log("Debug test: Monitoring network requests...\n");

  const client = await connect(SERVER_URL);
  const page = await client.page("network-debug", { viewport: { width: 1440, height: 900 } });

  // Track network requests
  const requests: string[] = [];
  page.on('request', request => {
    const url = request.url();
    if (url.includes('/discovery/')) {
      requests.push(`${request.method()} ${url}`);
      console.log(`[REQUEST] ${request.method()} ${url}`);
    }
  });

  page.on('response', response => {
    const url = response.url();
    if (url.includes('/discovery/')) {
      console.log(`[RESPONSE] ${response.status()} ${url}`);
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
    console.log("✅ Logged in\n");

    // Create new session
    const newSessionBtn = page.locator('button:has-text("New Session"), button:has-text("Create First Session")').first();
    await newSessionBtn.click();
    await page.waitForURL("**/upload", { timeout: 10000 });
    await waitForPageLoad(page);

    const sessionUrl = page.url();
    const sessionIdMatch = sessionUrl.match(/discovery\/([a-f0-9-]+)\/upload/);
    const sessionId = sessionIdMatch ? sessionIdMatch[1] : "unknown";
    console.log("✅ Created session: " + sessionId + "\n");

    // Upload file
    console.log("📤 Uploading file...");
    const fileInput = page.locator('input[type="file"]');
    await fileInput.setInputFiles(TEST_CSV);
    await page.waitForSelector('text=rows detected', { timeout: 20000 });
    console.log("✅ File uploaded\n");

    // Wait for any auto-triggered requests
    await page.waitForTimeout(1000);

    // Select Role mapping
    console.log("🔧 Selecting Role mapping...");
    const selects = page.locator('select');
    for (let i = 0; i < await selects.count(); i++) {
      const select = selects.nth(i);
      const parentText = await select.locator('..').textContent();
      if (parentText?.includes('Job Title')) {
        await select.selectOption('role');
        console.log("   Selected Job Title -> Role\n");
        break;
      }
    }

    // Wait for auto-save network request
    console.log("⏳ Waiting for auto-save request (2 seconds)...\n");
    await page.waitForTimeout(2000);

    // Check backend for mappings
    console.log("📋 Checking backend for saved mappings...");
    const uploadsRes = await fetch(`${API_URL}/discovery/sessions/${sessionId}/uploads`);
    const uploads = await uploadsRes.json();
    console.log("   Upload ID: " + uploads[0]?.id);
    console.log("   column_mappings: " + JSON.stringify(uploads[0]?.column_mappings));

    // Summary
    console.log("\n" + "=".repeat(50));
    console.log("SUMMARY OF DISCOVERY API REQUESTS:");
    console.log("=".repeat(50));
    const putRequests = requests.filter(r => r.includes('PUT'));
    if (putRequests.length > 0) {
      console.log("PUT requests made:");
      putRequests.forEach(r => console.log("  " + r));
    } else {
      console.log("NO PUT requests made to save mappings!");
      console.log("\nAll requests:");
      requests.forEach(r => console.log("  " + r));
    }

  } catch (error) {
    console.error("❌ Error:", error);
  } finally {
    await client.disconnect();
  }
}

runTest().catch(console.error);
