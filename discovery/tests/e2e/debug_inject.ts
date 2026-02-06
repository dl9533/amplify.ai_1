/**
 * Debug test that injects JS to monitor state changes.
 */
import { connect, waitForPageLoad } from "@/client.js";

const SERVER_URL = "http://localhost:9222";
const FRONTEND_URL = "http://localhost:5173";
const API_URL = "http://localhost:8001";
const TEST_CSV = "/Users/dl9533/projects/amplify.ai_1/discovery/tests/e2e/test_data/tech_startup_workforce.csv";

async function runTest() {
  console.log("Debug inject test...\n");

  const client = await connect(SERVER_URL);
  const page = await client.page("debug-inject", { viewport: { width: 1440, height: 900 } });

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

    await page.waitForTimeout(1000);

    // Get upload ID from API
    const uploadsRes = await fetch(API_URL + "/discovery/sessions/" + sessionId + "/uploads");
    const uploads = await uploadsRes.json();
    const uploadId = uploads[0]?.id;
    console.log("   Backend upload ID: " + uploadId);

    // Inject a PUT request directly to test the endpoint
    console.log("\n🔧 Testing direct PUT request from browser...");
    const putResult = await page.evaluate(async (data: { uploadId: string }) => {
      try {
        const res = await fetch("/discovery/uploads/" + data.uploadId + "/mappings", {
          method: "PUT",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify({ role: "Job Title", department: "Department" })
        });
        const text = await res.text();
        return { status: res.status, body: text };
      } catch (error: any) {
        return { error: error.message };
      }
    }, { uploadId });

    console.log("   PUT result:", JSON.stringify(putResult, null, 2));

    // Check if it worked
    const uploadsRes2 = await fetch(API_URL + "/discovery/sessions/" + sessionId + "/uploads");
    const uploads2 = await uploadsRes2.json();
    console.log("\n📋 column_mappings after direct PUT: " + JSON.stringify(uploads2[0]?.column_mappings));

    if (uploads2[0]?.column_mappings?.role) {
      console.log("\n✅ Direct PUT works!");
      console.log("   This means the frontend's auto-save isn't calling the API.");
    }

  } catch (error) {
    console.error("❌ Error:", error);
  } finally {
    await client.disconnect();
  }
}

runTest().catch(console.error);
