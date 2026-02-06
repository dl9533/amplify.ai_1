/**
 * Test the auto-save column mapping functionality.
 * This test verifies that column mappings are automatically saved
 * when the user selects them in the UI.
 */
import { connect, waitForPageLoad } from "@/client.js";

const SERVER_URL = "http://localhost:9222";
const FRONTEND_URL = "http://localhost:5173";
const API_URL = "http://localhost:8001";
const TEST_CSV = "/Users/dl9533/projects/amplify.ai_1/discovery/tests/e2e/test_data/tech_startup_workforce.csv";

async function runTest() {
  console.log("Testing auto-save column mapping functionality...\n");

  const client = await connect(SERVER_URL);
  const page = await client.page("autosave-test", { viewport: { width: 1440, height: 900 } });

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

    const sessionUrl = page.url();
    const sessionIdMatch = sessionUrl.match(/discovery\/([a-f0-9-]+)\/upload/);
    const sessionId = sessionIdMatch ? sessionIdMatch[1] : "unknown";
    console.log("✅ Created session: " + sessionId);

    // Upload file
    const fileInput = page.locator('input[type="file"]');
    await fileInput.setInputFiles(TEST_CSV);
    await page.waitForSelector('text=rows detected', { timeout: 20000 });
    console.log("✅ File uploaded");

    // Get the upload ID from the API
    const uploadsRes = await fetch(API_URL + "/discovery/sessions/" + sessionId + "/uploads");
    const uploads = await uploadsRes.json();
    const uploadId = uploads[0]?.id;
    console.log("   Upload ID: " + uploadId);

    // Check mappings BEFORE selecting in UI
    console.log("\n📋 Mappings BEFORE UI selection:");
    const uploadResBefore = await fetch(API_URL + "/discovery/sessions/" + sessionId + "/uploads");
    const uploadDataBefore = await uploadResBefore.json();
    console.log("   column_mappings: " + JSON.stringify(uploadDataBefore[0]?.column_mappings));

    // Select column mappings in the UI (this should trigger auto-save)
    const selects = page.locator('select');
    const selectCount = await selects.count();
    console.log("\n🔧 Mapping " + selectCount + " columns in UI...");

    // Map Job Title -> Role
    for (let i = 0; i < selectCount; i++) {
      const select = selects.nth(i);
      const parentText = await select.locator('..').textContent();

      if (parentText?.includes('Job Title')) {
        await select.selectOption('role');
        console.log('   Selected: Job Title -> Role');
      } else if (parentText?.includes('Department')) {
        await select.selectOption('department');
        console.log('   Selected: Department -> Department');
      } else if (parentText?.includes('Line of Business') || parentText?.includes('LOB')) {
        await select.selectOption('lob');
        console.log('   Selected: LOB -> Line of Business');
      } else if (parentText?.includes('Location')) {
        await select.selectOption('geography');
        console.log('   Selected: Location -> Geography');
      } else if (parentText?.includes('Employee Count') || parentText?.includes('Headcount')) {
        await select.selectOption('headcount');
        console.log('   Selected: Headcount -> Headcount');
      }
    }

    // Wait for debounced auto-save (500ms debounce + 500ms buffer)
    console.log('\n⏳ Waiting for auto-save (1.5 seconds)...');
    await page.waitForTimeout(1500);

    // Check mappings AFTER selecting in UI
    console.log("\n📋 Mappings AFTER UI selection:");
    const uploadRes = await fetch(API_URL + "/discovery/sessions/" + sessionId + "/uploads");
    const uploadData = await uploadRes.json();
    console.log("   column_mappings: " + JSON.stringify(uploadData[0]?.column_mappings));

    const hasMappings = uploadData[0]?.column_mappings && Object.keys(uploadData[0].column_mappings).length > 0;

    if (hasMappings) {
      console.log("\n✅ AUTO-SAVE WORKING: Column mappings were saved to backend!");

      // Now click Continue and verify role mappings are generated
      await page.click('button:has-text("Continue")');
      await page.waitForURL("**/map-roles", { timeout: 15000 });
      await waitForPageLoad(page);
      console.log("\n✅ Navigated to Map Roles step");

      // Wait for role mappings to generate (the hook auto-triggers generation)
      console.log("⏳ Waiting for role mappings to generate...");
      await page.waitForTimeout(5000);

      // Check if role mappings were generated
      const mappingsRes = await fetch(API_URL + "/discovery/sessions/" + sessionId + "/role-mappings");
      const mappings = await mappingsRes.json();
      console.log("\n📋 Role mappings generated: " + mappings.length + " roles");

      if (mappings.length > 0) {
        const withOnet = mappings.filter((m: any) => m.onet_code !== null).length;
        console.log("   With O*NET codes: " + withOnet + "/" + mappings.length);
        console.log("\n🎉 SUCCESS: Full flow working - auto-save enabled role mapping generation!");
      } else {
        console.log("\n⚠️ No role mappings generated yet - checking if generation was triggered...");

        // Try manually triggering generation
        const genRes = await fetch(API_URL + "/discovery/sessions/" + sessionId + "/role-mappings/generate", {
          method: "POST",
          headers: { "Content-Type": "application/json" }
        });
        if (genRes.ok) {
          const genData = await genRes.json();
          console.log("   Manually triggered: " + genData.created_count + " mappings created");
        }
      }
    } else {
      console.log("\n❌ AUTO-SAVE NOT WORKING: Mappings were NOT saved to backend");
      console.log("   This may indicate the auto-save useEffect is not firing correctly.");
    }

    await page.screenshot({ path: "tmp/autosave_test_result.png" });
    console.log("\nScreenshot saved to: tmp/autosave_test_result.png");

  } catch (error) {
    console.error("\n❌ Test failed:", error);
    await page.screenshot({ path: "tmp/autosave_test_error.png" });
  } finally {
    await client.disconnect();
  }
}

runTest().catch(console.error);
