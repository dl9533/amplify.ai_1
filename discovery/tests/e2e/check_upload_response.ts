/**
 * Check what the frontend receives from the upload endpoint.
 */
import { connect, waitForPageLoad } from "@/client.js";

const SERVER_URL = "http://localhost:9222";
const FRONTEND_URL = "http://localhost:5173";
const API_URL = "http://localhost:8001";
const TEST_CSV = "/Users/dl9533/projects/amplify.ai_1/discovery/tests/e2e/test_data/tech_startup_workforce.csv";

async function runTest() {
  console.log("Check upload response test...\n");

  const client = await connect(SERVER_URL);
  const page = await client.page("check-upload", { viewport: { width: 1440, height: 900 } });

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

    // Intercept and log the upload response
    let uploadResponse: any = null;
    page.on('response', async (response) => {
      if (response.url().includes('/upload') && response.request().method() === 'POST') {
        try {
          const body = await response.json();
          uploadResponse = body;
          console.log("\n📦 Intercepted upload response:");
          console.log("   Keys:", Object.keys(body));
          console.log("   id:", body.id);
          console.log("   file_name:", body.file_name);
          console.log("   Full response:", JSON.stringify(body, null, 2));
        } catch (e) {
          console.log("   Could not parse response as JSON");
        }
      }
    });

    // Upload
    console.log("\n📤 Uploading file...");
    await page.locator('input[type="file"]').setInputFiles(TEST_CSV);
    await page.waitForSelector('text=rows detected', { timeout: 20000 });
    console.log("✅ Uploaded");

    // Wait for response to be captured
    await page.waitForTimeout(1000);

    // Compare with backend
    const uploadsRes = await fetch(API_URL + "/discovery/sessions/" + sessionId + "/uploads");
    const uploads = await uploadsRes.json();
    console.log("\n📋 Backend upload record:");
    console.log("   id:", uploads[0]?.id);

    // Check if IDs match
    if (uploadResponse && uploadResponse.id === uploads[0]?.id) {
      console.log("\n✅ Upload response has correct ID");
    } else {
      console.log("\n❌ ID mismatch or not found in response");
      console.log("   Response ID:", uploadResponse?.id);
      console.log("   Backend ID:", uploads[0]?.id);
    }

  } catch (error) {
    console.error("❌ Error:", error);
  } finally {
    await client.disconnect();
  }
}

runTest().catch(console.error);
