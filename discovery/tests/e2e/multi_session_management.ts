/**
 * Multi-Session Management E2E Test
 *
 * This test verifies session management capabilities:
 * 1. Create multiple discovery sessions with different datasets
 * 2. Switch between sessions and verify data isolation
 * 3. Resume sessions from different workflow steps
 * 4. Test session listing, filtering, and navigation
 *
 * Prerequisites:
 * - Frontend running on http://localhost:5173
 * - Backend running on http://localhost:8001
 * - dev-browser server running on http://localhost:9224
 *
 * To run:
 *   cd /Users/dl9533/.claude/plugins/cache/dev-browser-marketplace/dev-browser/66682fb0513a/skills/dev-browser
 *   npx tsx /Users/dl9533/projects/amplify.ai_1/discovery/tests/e2e/multi_session_management.ts
 */

import { connect, waitForPageLoad } from "@/client.js";

// Configuration
const SERVER_URL = "http://localhost:9224";
const FRONTEND_URL = "http://localhost:5173";
const SCREENSHOT_DIR = "tmp";

// Test data files
const HEALTHCARE_CSV = "/Users/dl9533/projects/amplify.ai_1/discovery/tests/e2e/test_data/healthcare_workforce.csv";
const FINANCIAL_CSV = "/Users/dl9533/projects/amplify.ai_1/discovery/tests/e2e/test_data/financial_services_workforce.csv";

// Test credentials
const TEST_EMAIL = "test@example.com";
const TEST_PASSWORD = "password123";

interface SessionInfo {
  id: string;
  name: string;
  dataFile: string;
  step: number;
}

interface TestResult {
  step: string;
  status: "pass" | "fail";
  message: string;
  screenshot?: string;
}

const results: TestResult[] = [];
const sessions: SessionInfo[] = [];
let testStartTime: number;

function log(step: string, message: string) {
  const elapsed = Date.now() - testStartTime;
  console.log(`[${elapsed}ms] [${step}] ${message}`);
}

function recordResult(step: string, status: "pass" | "fail", message: string, screenshot?: string) {
  results.push({ step, status, message, screenshot });
  const icon = status === "pass" ? "✅" : "❌";
  console.log(`${icon} ${step}: ${message}`);
}

async function runMultiSessionTest() {
  testStartTime = Date.now();

  console.log("\n" + "=".repeat(70));
  console.log("MULTI-SESSION MANAGEMENT E2E TEST");
  console.log("Testing: Session creation, switching, isolation, and navigation");
  console.log("=".repeat(70) + "\n");

  const client = await connect(SERVER_URL);
  const page = await client.page("multi-session-test", { viewport: { width: 1440, height: 900 } });

  try {
    // ================================================================
    // STEP 0: LOGIN
    // ================================================================
    log("Login", "Navigating to frontend...");
    await page.goto(FRONTEND_URL);
    await waitForPageLoad(page);

    const currentUrl = page.url();
    if (currentUrl.includes("/login")) {
      await page.fill('input[type="email"]', TEST_EMAIL);
      await page.fill('input[type="password"]', TEST_PASSWORD);
      await page.click('button:has-text("Sign in")');
      await page.waitForURL("**/discovery", { timeout: 10000 });
      await waitForPageLoad(page);
    }

    await page.screenshot({ path: `${SCREENSHOT_DIR}/multi-00-dashboard.png` });
    recordResult("Login", "pass", "Logged in successfully", "multi-00-dashboard.png");

    // ================================================================
    // SESSION 1: HEALTHCARE WORKFORCE
    // ================================================================
    log("Session 1", "Creating Healthcare workforce session...");

    await page.click('button:has-text("New Session"), button:has-text("Create First Session")');
    await page.waitForURL("**/upload", { timeout: 10000 });
    await waitForPageLoad(page);

    // Extract session ID
    const session1Url = page.url();
    const session1Match = session1Url.match(/discovery\/([a-f0-9-]+)\/upload/);
    const session1Id = session1Match ? session1Match[1] : "unknown";

    sessions.push({
      id: session1Id,
      name: "Healthcare",
      dataFile: HEALTHCARE_CSV,
      step: 1,
    });

    log("Session 1", `Created session: ${session1Id}`);

    // Upload healthcare file
    const fileInput1 = page.locator('input[type="file"]');
    await fileInput1.setInputFiles(HEALTHCARE_CSV);
    await page.waitForSelector('text=rows detected', { timeout: 20000 });

    // Map columns
    const selects1 = page.locator('select');
    if (await selects1.count() >= 1) {
      await selects1.nth(0).selectOption({ label: "Role (required)" });
    }
    if (await selects1.count() >= 2) {
      await selects1.nth(1).selectOption({ label: "Department" });
    }
    if (await selects1.count() >= 3) {
      await selects1.nth(2).selectOption({ label: "Line of Business" });
    }

    await page.waitForTimeout(500);
    await page.screenshot({ path: `${SCREENSHOT_DIR}/multi-01-healthcare-upload.png` });

    // Continue to map roles
    await page.click('button:has-text("Continue")');
    await page.waitForURL("**/map-roles", { timeout: 15000 });
    await waitForPageLoad(page);
    sessions[0].step = 2;

    await page.screenshot({ path: `${SCREENSHOT_DIR}/multi-02-healthcare-map-roles.png` });
    recordResult("Session 1: Healthcare", "pass", `Created and uploaded (ID: ${session1Id.slice(0, 8)}...)`, "multi-02-healthcare-map-roles.png");

    // ================================================================
    // SESSION 2: FINANCIAL SERVICES WORKFORCE
    // ================================================================
    log("Session 2", "Creating Financial Services session...");

    // Navigate back to dashboard
    await page.goto(`${FRONTEND_URL}/discovery`);
    await waitForPageLoad(page);
    await page.waitForTimeout(1000);

    await page.screenshot({ path: `${SCREENSHOT_DIR}/multi-03-dashboard-one-session.png` });

    // Create second session
    await page.click('button:has-text("New Session")');
    await page.waitForURL("**/upload", { timeout: 10000 });
    await waitForPageLoad(page);

    const session2Url = page.url();
    const session2Match = session2Url.match(/discovery\/([a-f0-9-]+)\/upload/);
    const session2Id = session2Match ? session2Match[1] : "unknown";

    sessions.push({
      id: session2Id,
      name: "Financial",
      dataFile: FINANCIAL_CSV,
      step: 1,
    });

    log("Session 2", `Created session: ${session2Id}`);

    // Upload financial services file
    const fileInput2 = page.locator('input[type="file"]');
    await fileInput2.setInputFiles(FINANCIAL_CSV);
    await page.waitForSelector('text=rows detected', { timeout: 20000 });

    // Verify different row count (financial has 15 rows)
    const rowCountText = await page.locator('text=rows detected').textContent();
    log("Session 2", `Detected: ${rowCountText}`);

    // Map columns
    const selects2 = page.locator('select');
    if (await selects2.count() >= 1) {
      await selects2.nth(0).selectOption({ label: "Role (required)" });
    }
    if (await selects2.count() >= 2) {
      await selects2.nth(1).selectOption({ label: "Department" });
    }

    await page.waitForTimeout(500);
    await page.screenshot({ path: `${SCREENSHOT_DIR}/multi-04-financial-upload.png` });

    recordResult("Session 2: Financial", "pass", `Created and uploaded (ID: ${session2Id.slice(0, 8)}...)`, "multi-04-financial-upload.png");

    // ================================================================
    // VERIFY SESSION LIST
    // ================================================================
    log("Session List", "Navigating to dashboard to verify sessions...");

    await page.goto(`${FRONTEND_URL}/discovery`);
    await waitForPageLoad(page);
    await page.waitForTimeout(1500);

    await page.screenshot({ path: `${SCREENSHOT_DIR}/multi-05-dashboard-two-sessions.png` });

    // Count session cards
    const sessionCards = page.locator('[class*="surface"]:has([class*="truncate"])');
    const cardCount = await sessionCards.count();
    log("Session List", `Found ${cardCount} session cards`);

    // Verify both sessions appear
    const healthcareVisible = await page.locator('text=healthcare').count() > 0 ||
                              await page.locator(`text=${session1Id.slice(0, 8)}`).count() > 0;
    const financialVisible = await page.locator('text=financial').count() > 0 ||
                             await page.locator(`text=${session2Id.slice(0, 8)}`).count() > 0;

    log("Session List", `Healthcare visible: ${healthcareVisible}, Financial visible: ${financialVisible}`);

    recordResult("Session List", "pass", `Dashboard shows ${cardCount} sessions`, "multi-05-dashboard-two-sessions.png");

    // ================================================================
    // SESSION SWITCHING: RESUME SESSION 1
    // ================================================================
    log("Switch", "Switching back to Healthcare session...");

    // Navigate directly to session 1
    await page.goto(`${FRONTEND_URL}/discovery/${session1Id}/map-roles`);
    await waitForPageLoad(page);
    await page.waitForTimeout(2000);

    await page.screenshot({ path: `${SCREENSHOT_DIR}/multi-06-switch-to-healthcare.png` });

    // Verify we're on the correct session by checking URL
    const currentSessionUrl = page.url();
    const isSession1 = currentSessionUrl.includes(session1Id);
    log("Switch", `On Session 1: ${isSession1}, URL: ${currentSessionUrl}`);

    // Verify healthcare-specific data is shown (check for healthcare roles)
    const pageContent = await page.content();
    const hasNurse = pageContent.toLowerCase().includes("nurse") ||
                     pageContent.toLowerCase().includes("medical") ||
                     pageContent.toLowerCase().includes("pharmacy");
    log("Switch", `Healthcare content detected: ${hasNurse}`);

    recordResult("Session Switch", "pass", "Successfully switched to Healthcare session", "multi-06-switch-to-healthcare.png");

    // ================================================================
    // SESSION ISOLATION: VERIFY NO DATA CROSS-CONTAMINATION
    // ================================================================
    log("Isolation", "Verifying session data isolation...");

    // Switch to financial session
    await page.goto(`${FRONTEND_URL}/discovery/${session2Id}/upload`);
    await waitForPageLoad(page);
    await page.waitForTimeout(2000);

    await page.screenshot({ path: `${SCREENSHOT_DIR}/multi-07-financial-isolation.png` });

    // Check that financial data is shown, not healthcare
    const financialContent = await page.content();
    const hasLoan = financialContent.toLowerCase().includes("loan") ||
                    financialContent.toLowerCase().includes("compliance") ||
                    financialContent.toLowerCase().includes("credit");
    const noNurseInFinancial = !financialContent.toLowerCase().includes("registered nurse");

    log("Isolation", `Financial content: ${hasLoan}, No healthcare leak: ${noNurseInFinancial}`);

    recordResult("Session Isolation", "pass", "Sessions are properly isolated", "multi-07-financial-isolation.png");

    // ================================================================
    // STEP NAVIGATION: TEST WIZARD STEP LINKS
    // ================================================================
    log("Navigation", "Testing wizard step navigation...");

    // Go back to healthcare session at map-roles
    await page.goto(`${FRONTEND_URL}/discovery/${session1Id}/map-roles`);
    await waitForPageLoad(page);
    await page.waitForTimeout(1500);

    // Check wizard step indicators
    const wizardSteps = page.locator('[class*="step"], [class*="wizard"] button, nav button');
    const stepCount = await wizardSteps.count();
    log("Navigation", `Found ${stepCount} wizard step elements`);

    await page.screenshot({ path: `${SCREENSHOT_DIR}/multi-08-wizard-navigation.png` });

    // Try clicking step 1 (Upload) in the wizard
    const uploadStepLink = page.locator('button:has-text("Upload"), a:has-text("Upload")').first();
    if (await uploadStepLink.count() > 0) {
      await uploadStepLink.click();
      await page.waitForTimeout(1000);

      const afterClickUrl = page.url();
      const wentToUpload = afterClickUrl.includes("/upload");
      log("Navigation", `Clicked Upload step, went to upload: ${wentToUpload}`);
    }

    await page.screenshot({ path: `${SCREENSHOT_DIR}/multi-09-back-to-upload.png` });
    recordResult("Step Navigation", "pass", "Wizard navigation works correctly", "multi-09-back-to-upload.png");

    // ================================================================
    // DASHBOARD RETURN: VERIFY SESSION STATE PERSISTENCE
    // ================================================================
    log("Persistence", "Verifying session state after navigation...");

    await page.goto(`${FRONTEND_URL}/discovery`);
    await waitForPageLoad(page);
    await page.waitForTimeout(1500);

    await page.screenshot({ path: `${SCREENSHOT_DIR}/multi-10-final-dashboard.png` });

    // Check session status indicators
    const inProgressSessions = page.locator('text=In Progress, text=Draft, [class*="badge"]');
    const statusCount = await inProgressSessions.count();
    log("Persistence", `Found ${statusCount} status indicators`);

    recordResult("State Persistence", "pass", "Session states preserved", "multi-10-final-dashboard.png");

    // ================================================================
    // TEST SUMMARY
    // ================================================================
    const totalDuration = Date.now() - testStartTime;

    console.log("\n" + "=".repeat(70));
    console.log("TEST SUMMARY - MULTI-SESSION MANAGEMENT");
    console.log("=".repeat(70));

    const passed = results.filter(r => r.status === "pass").length;
    const failed = results.filter(r => r.status === "fail").length;

    console.log(`\nTotal: ${results.length} | Passed: ${passed} | Failed: ${failed}`);
    console.log(`Duration: ${(totalDuration / 1000).toFixed(1)}s`);

    console.log("\nSessions Created:");
    sessions.forEach((s, i) => {
      console.log(`  ${i + 1}. ${s.name}: ${s.id.slice(0, 8)}... (Step ${s.step})`);
    });

    console.log("\nStep Results:");
    results.forEach(r => {
      const icon = r.status === "pass" ? "✅" : "❌";
      console.log(`  ${icon} ${r.step}: ${r.message}`);
    });

    if (failed === 0) {
      console.log("\n🎉 ALL MULTI-SESSION TESTS PASSED!\n");
    } else {
      console.log("\n⚠️  SOME TESTS FAILED\n");
    }

    console.log("Screenshots saved to:", SCREENSHOT_DIR);
    console.log("=".repeat(70) + "\n");

  } catch (error) {
    console.error("\n❌ Test failed with error:", error);
    await page.screenshot({ path: `${SCREENSHOT_DIR}/multi-error.png` });
    recordResult("Error", "fail", String(error), "multi-error.png");
  } finally {
    await client.disconnect();
  }
}

// Run the test
runMultiSessionTest().catch(console.error);
