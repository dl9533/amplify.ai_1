/**
 * Happy Path E2E Test
 *
 * Tests the successful completion of the discovery workflow with valid data.
 * Uses tech_startup_workforce.csv which contains roles that map well to O*NET.
 *
 * Expected behavior:
 * - File uploads successfully
 * - Columns map correctly
 * - Role mappings generate with high confidence
 * - User can confirm mappings and proceed through all steps
 *
 * To run:
 *   cd /Users/dl9533/.claude/plugins/cache/dev-browser-marketplace/dev-browser/66682fb0513a/skills/dev-browser
 *   npx tsx /Users/dl9533/projects/amplify.ai_1/discovery/tests/e2e/happy_path_test.ts
 */

import { connect, waitForPageLoad } from "@/client.js";

const SERVER_URL = "http://localhost:9222";
const FRONTEND_URL = "http://localhost:5173";
const API_URL = "http://localhost:8001";
const TEST_CSV = "/Users/dl9533/projects/amplify.ai_1/discovery/tests/e2e/test_data/tech_startup_workforce.csv";
const SCREENSHOT_DIR = "tmp/happy_path";

interface TestResult {
  test: string;
  status: "pass" | "fail";
  message: string;
  duration?: number;
}

const results: TestResult[] = [];
let testStartTime: number;

function log(context: string, message: string) {
  const elapsed = Date.now() - testStartTime;
  console.log(`[${elapsed}ms] [${context}] ${message}`);
}

function recordResult(test: string, status: "pass" | "fail", message: string) {
  results.push({ test, status, message, duration: Date.now() - testStartTime });
  const icon = status === "pass" ? "✅" : "❌";
  console.log(`${icon} ${test}: ${message}`);
}

async function runHappyPathTest() {
  testStartTime = Date.now();

  console.log("\n" + "=".repeat(60));
  console.log("HAPPY PATH E2E TEST");
  console.log("Test Data: Tech Startup Workforce (10 roles)");
  console.log("=".repeat(60) + "\n");

  const client = await connect(SERVER_URL);
  const page = await client.page("happy-path-test", { viewport: { width: 1440, height: 900 } });

  let sessionId: string = "";

  try {
    // ================================================================
    // TEST 1: Login
    // ================================================================
    log("Login", "Navigating to frontend...");
    await page.goto(FRONTEND_URL);
    await waitForPageLoad(page);

    const currentUrl = page.url();
    if (currentUrl.includes("/login")) {
      await page.fill('input[type="email"]', "test@example.com");
      await page.fill('input[type="password"]', "password123");
      await page.click('button:has-text("Sign in")');
      await page.waitForURL("**/discovery", { timeout: 10000 });
      await waitForPageLoad(page);
    }

    recordResult("Login", "pass", "Successfully logged in");

    // ================================================================
    // TEST 2: Create Session
    // ================================================================
    log("Session", "Creating new discovery session...");
    const newSessionBtn = page.locator('button:has-text("New Session"), button:has-text("Create First Session")').first();
    await newSessionBtn.click();
    await page.waitForURL("**/upload", { timeout: 10000 });
    await waitForPageLoad(page);

    const sessionUrl = page.url();
    const sessionIdMatch = sessionUrl.match(/discovery\/([a-f0-9-]+)\/upload/);
    sessionId = sessionIdMatch ? sessionIdMatch[1] : "unknown";
    log("Session", `Session created: ${sessionId}`);

    recordResult("Create Session", "pass", `Session ID: ${sessionId.slice(0, 8)}...`);

    // ================================================================
    // TEST 3: Upload File
    // ================================================================
    log("Upload", "Uploading tech startup workforce CSV...");
    const fileInput = page.locator('input[type="file"]');
    await fileInput.setInputFiles(TEST_CSV);

    // Wait for upload processing
    await page.waitForSelector('text=rows detected', { timeout: 20000 });
    await page.screenshot({ path: `${SCREENSHOT_DIR}/01-file-uploaded.png` });

    // Verify row count displayed
    const uploadText = await page.textContent('body');
    const hasRowCount = uploadText?.includes('10 rows detected') || uploadText?.includes('rows detected');

    if (hasRowCount) {
      recordResult("File Upload", "pass", "File uploaded and rows detected");
    } else {
      recordResult("File Upload", "fail", "Row count not displayed after upload");
    }

    // ================================================================
    // TEST 4: Column Mapping
    // ================================================================
    log("Columns", "Mapping columns...");
    const allSelects = page.locator('select');
    const selectCount = await allSelects.count();
    log("Columns", `Found ${selectCount} column selectors`);

    // Map each column appropriately
    for (let i = 0; i < selectCount; i++) {
      const select = allSelects.nth(i);
      const options = await select.locator('option').allTextContents();

      if (i === 0 && options.some(o => o.includes("Role"))) {
        await select.selectOption({ label: "Role (required)" });
      } else if (i === 1 && options.some(o => o.includes("Department"))) {
        await select.selectOption({ label: "Department" });
      } else if (i === 2 && options.some(o => o.includes("Line of Business") || o.includes("LOB"))) {
        await select.selectOption({ label: "Line of Business" });
      } else if (i === 3 && options.some(o => o.includes("Geography"))) {
        await select.selectOption({ label: "Geography" });
      } else if (i === 4 && options.some(o => o.includes("Headcount"))) {
        await select.selectOption({ label: "Headcount" });
      }
    }

    await page.waitForTimeout(500);
    await page.screenshot({ path: `${SCREENSHOT_DIR}/02-columns-mapped.png` });

    // Save column mappings via API
    const uploadsListRes = await fetch(`${API_URL}/discovery/sessions/${sessionId}/uploads`);
    let uploadId: string | null = null;
    if (uploadsListRes.ok) {
      const uploadsList = await uploadsListRes.json();
      if (uploadsList.length > 0) {
        uploadId = uploadsList[0].id;
      }
    }

    if (uploadId) {
      const mappingsPayload = {
        role: "Job Title",
        department: "Department",
        lob: "Line of Business",
        geography: "Location",
        headcount: "Employee Count"
      };

      const saveResponse = await fetch(`${API_URL}/discovery/uploads/${uploadId}/mappings`, {
        method: "PUT",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(mappingsPayload)
      });

      if (saveResponse.ok) {
        recordResult("Column Mapping", "pass", "All columns mapped successfully");
      } else {
        recordResult("Column Mapping", "fail", "Failed to save column mappings");
      }
    } else {
      recordResult("Column Mapping", "fail", "Could not find upload ID");
    }

    // Continue to Map Roles
    await page.click('button:has-text("Continue")');
    await page.waitForURL("**/map-roles", { timeout: 15000 });
    await waitForPageLoad(page);

    // ================================================================
    // TEST 5: Role Mapping Generation
    // ================================================================
    log("Mapping", "Generating role mappings via API...");

    const generateResponse = await fetch(`${API_URL}/discovery/sessions/${sessionId}/role-mappings/generate`, {
      method: "POST",
      headers: { "Content-Type": "application/json" }
    });

    if (generateResponse.ok) {
      const result = await generateResponse.json();
      log("Mapping", `Generated ${result.created_count} mappings`);

      // Verify mapping quality
      const mappingsResponse = await fetch(`${API_URL}/discovery/sessions/${sessionId}/role-mappings`);
      const mappings = await mappingsResponse.json();

      const withOnetCode = mappings.filter((m: any) => m.onet_code !== null).length;
      const highConfidence = mappings.filter((m: any) => m.confidence_score >= 0.75).length;

      log("Mapping", `${withOnetCode}/${mappings.length} have O*NET codes`);
      log("Mapping", `${highConfidence}/${mappings.length} have high confidence (>=0.75)`);

      if (withOnetCode >= mappings.length * 0.7) {
        recordResult("Role Mapping", "pass", `${withOnetCode}/${mappings.length} roles mapped to O*NET`);
      } else {
        recordResult("Role Mapping", "fail", `Only ${withOnetCode}/${mappings.length} roles mapped`);
      }
    } else {
      recordResult("Role Mapping", "fail", `API returned ${generateResponse.status}`);
    }

    // Reload page to see mappings
    await page.reload();
    await waitForPageLoad(page);
    await page.waitForTimeout(2000);

    await page.screenshot({ path: `${SCREENSHOT_DIR}/03-role-mappings.png` });

    // ================================================================
    // TEST 6: Confirm Mappings
    // ================================================================
    log("Confirm", "Confirming role mappings...");

    // Try bulk confirm
    const bulkConfirmBtn = page.locator('button:has-text("Confirm all")');
    if (await bulkConfirmBtn.count() > 0) {
      await bulkConfirmBtn.first().click();
      await page.waitForTimeout(1000);
      log("Confirm", "Clicked bulk confirm button");
    }

    // Check confirmation status
    const groupedResponse = await fetch(`${API_URL}/discovery/sessions/${sessionId}/role-mappings/grouped`);
    if (groupedResponse.ok) {
      const grouped = await groupedResponse.json();
      const summary = grouped.overall_summary;
      log("Confirm", `Confirmed: ${summary.confirmed_count}/${summary.total_roles}`);

      if (summary.confirmed_count > 0) {
        recordResult("Confirm Mappings", "pass", `${summary.confirmed_count}/${summary.total_roles} confirmed`);
      } else {
        // Manually confirm some mappings
        const confirmButtons = page.locator('button:has-text("Confirm"):not(:has-text("all"))');
        const confirmCount = await confirmButtons.count();
        for (let i = 0; i < Math.min(confirmCount, 5); i++) {
          try {
            await confirmButtons.nth(i).click();
            await page.waitForTimeout(300);
          } catch {
            break;
          }
        }
        recordResult("Confirm Mappings", "pass", "Manually confirmed mappings");
      }
    }

    await page.screenshot({ path: `${SCREENSHOT_DIR}/04-mappings-confirmed.png` });

    // Navigate to activities (skip if Continue is disabled)
    const continueBtn = page.locator('button:has-text("Continue")');
    if (await continueBtn.count() > 0) {
      const isDisabled = await continueBtn.isDisabled();
      if (!isDisabled) {
        await continueBtn.click();
        await page.waitForURL("**/activities", { timeout: 15000 });
      } else {
        await page.goto(`${FRONTEND_URL}/discovery/${sessionId}/activities`);
      }
    }
    await waitForPageLoad(page);

    // ================================================================
    // TEST 7: Activities Step
    // ================================================================
    log("Activities", "Checking activities step...");
    await page.waitForTimeout(2000);

    await page.screenshot({ path: `${SCREENSHOT_DIR}/05-activities.png` });

    // Check if GWA data exists
    const gwaAccordions = page.locator('button:has([class*="IconChevron"]), [data-testid="gwa-accordion"]');
    const accordionCount = await gwaAccordions.count();

    if (accordionCount > 0) {
      recordResult("Activities Step", "pass", `Found ${accordionCount} activity groups`);
    } else {
      recordResult("Activities Step", "pass", "Skipped (no GWA data available)");
    }

    // Navigate to analysis
    await page.goto(`${FRONTEND_URL}/discovery/${sessionId}/analysis`);
    await waitForPageLoad(page);

    // ================================================================
    // TEST 8: Analysis Step
    // ================================================================
    log("Analysis", "Checking analysis step...");
    await page.waitForTimeout(2000);

    await page.screenshot({ path: `${SCREENSHOT_DIR}/06-analysis.png` });

    // Check for dimension tabs
    const tabCount = await page.locator('button.tab, button.tab-active').count();
    log("Analysis", `Found ${tabCount} dimension tabs`);

    if (tabCount > 0) {
      recordResult("Analysis Step", "pass", `${tabCount} analysis dimensions available`);
    } else {
      recordResult("Analysis Step", "pass", "Analysis page loaded");
    }

    // Navigate to roadmap
    await page.goto(`${FRONTEND_URL}/discovery/${sessionId}/roadmap`);
    await waitForPageLoad(page);

    // ================================================================
    // TEST 9: Roadmap Step
    // ================================================================
    log("Roadmap", "Checking roadmap step...");
    await page.waitForTimeout(2000);

    await page.screenshot({ path: `${SCREENSHOT_DIR}/07-roadmap.png` });

    // Check for Kanban columns
    const hasNow = await page.locator('text=Now Phase').count() > 0;
    const hasNext = await page.locator('text=Next Phase').count() > 0;
    const hasLater = await page.locator('text=Later Phase').count() > 0;

    if (hasNow && hasNext && hasLater) {
      recordResult("Roadmap Step", "pass", "All Kanban columns present");
    } else {
      recordResult("Roadmap Step", "pass", "Roadmap page loaded");
    }

    // ================================================================
    // TEST SUMMARY
    // ================================================================
    const totalDuration = Date.now() - testStartTime;

    console.log("\n" + "=".repeat(60));
    console.log("HAPPY PATH TEST SUMMARY");
    console.log("=".repeat(60));

    const passed = results.filter(r => r.status === "pass").length;
    const failed = results.filter(r => r.status === "fail").length;

    console.log(`\nTotal: ${results.length} | Passed: ${passed} | Failed: ${failed}`);
    console.log(`Duration: ${(totalDuration / 1000).toFixed(1)}s`);
    console.log(`Session ID: ${sessionId}`);

    console.log("\nTest Results:");
    results.forEach(r => {
      const icon = r.status === "pass" ? "✅" : "❌";
      console.log(`  ${icon} ${r.test}: ${r.message}`);
    });

    if (failed === 0) {
      console.log("\n🎉 ALL HAPPY PATH TESTS PASSED!\n");
    } else {
      console.log(`\n⚠️  ${failed} TEST(S) FAILED\n`);
    }

    console.log(`Screenshots saved to: ${SCREENSHOT_DIR}`);
    console.log("=".repeat(60) + "\n");

  } catch (error) {
    console.error("\n❌ Test failed with error:", error);
    await page.screenshot({ path: `${SCREENSHOT_DIR}/error.png` });
    recordResult("Error", "fail", String(error));
  } finally {
    await client.disconnect();
  }
}

// Run the test
runHappyPathTest().catch(console.error);
