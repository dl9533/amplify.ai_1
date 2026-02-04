/**
 * Discovery Frontend E2E Happy Path Test
 *
 * This test exercises the complete discovery workflow via the frontend UI:
 * 1. Login
 * 2. Create a new session
 * 3. Upload workforce CSV file
 * 4. Map columns (role, department, geography, headcount)
 * 5. Proceed to Map Roles step
 *
 * Prerequisites:
 * - Frontend running on http://localhost:5173
 * - Backend running on http://localhost:8001
 * - dev-browser server running on http://localhost:9224
 *
 * To run:
 *   cd /Users/dl9533/.claude/plugins/cache/dev-browser-marketplace/dev-browser/66682fb0513a/skills/dev-browser
 *   npx tsx /Users/dl9533/projects/amplify.ai_1/discovery/tests/e2e/frontend_happy_path.ts
 */

import { connect, waitForPageLoad } from "@/client.js";

// Configuration
const SERVER_URL = "http://localhost:9224";  // dev-browser server
const FRONTEND_URL = "http://localhost:5173";
const TEST_CSV = "/Users/dl9533/projects/amplify.ai_1/discovery/tests/e2e/test_data/workforce_with_lob.csv";
const SCREENSHOT_DIR = "tmp";

// Test credentials (dev mode accepts any email/password)
const TEST_EMAIL = "test@example.com";
const TEST_PASSWORD = "password123";

interface TestResult {
  step: string;
  status: "pass" | "fail";
  message: string;
  screenshot?: string;
}

const results: TestResult[] = [];

function log(step: string, message: string) {
  console.log(`[${step}] ${message}`);
}

function recordResult(step: string, status: "pass" | "fail", message: string, screenshot?: string) {
  results.push({ step, status, message, screenshot });
  const icon = status === "pass" ? "✅" : "❌";
  console.log(`${icon} ${step}: ${message}`);
}

async function runHappyPathTest() {
  console.log("\n" + "=".repeat(60));
  console.log("DISCOVERY FRONTEND E2E HAPPY PATH TEST");
  console.log("=".repeat(60) + "\n");

  const client = await connect(SERVER_URL);
  const page = await client.page("discovery-e2e", { viewport: { width: 1280, height: 900 } });

  try {
    // ============================================================
    // STEP 1: Navigate to App
    // ============================================================
    log("Step 1", "Navigating to frontend...");
    await page.goto(FRONTEND_URL);
    await waitForPageLoad(page);

    const currentUrl = page.url();
    let isLoggedIn = !currentUrl.includes("/login");

    if (isLoggedIn) {
      // Already logged in - logout first for clean test
      log("Step 1", "Already logged in, logging out first...");
      const signOutBtn = page.locator('button:has-text("Sign out")');
      if (await signOutBtn.count() > 0) {
        await signOutBtn.click();
        await page.waitForURL("**/login", { timeout: 5000 });
        await waitForPageLoad(page);
        isLoggedIn = false;
      }
    }

    if (!isLoggedIn) {
      await page.screenshot({ path: `${SCREENSHOT_DIR}/e2e-01-login.png` });
      recordResult("Navigate to Login", "pass", `Reached login page: ${page.url()}`, "e2e-01-login.png");
    }

    // ============================================================
    // STEP 2: Login
    // ============================================================
    log("Step 2", "Logging in...");

    // Fill login form
    await page.fill('input[type="email"]', TEST_EMAIL);
    await page.fill('input[type="password"]', TEST_PASSWORD);
    await page.screenshot({ path: `${SCREENSHOT_DIR}/e2e-02-login-filled.png` });

    // Click sign in
    await page.click('button:has-text("Sign in")');

    // Wait for dashboard
    await page.waitForURL("**/discovery", { timeout: 10000 });
    await waitForPageLoad(page);

    await page.screenshot({ path: `${SCREENSHOT_DIR}/e2e-03-dashboard.png` });
    recordResult("Login", "pass", `Logged in as ${TEST_EMAIL}`, "e2e-03-dashboard.png");

    // ============================================================
    // STEP 3: Create New Session
    // ============================================================
    log("Step 3", "Creating new session...");

    // Click "New Session" button
    await page.click('button:has-text("New Session"), button:has-text("Create First Session")');

    // Wait for upload page
    await page.waitForURL("**/upload", { timeout: 10000 });
    await waitForPageLoad(page);

    const sessionUrl = page.url();
    const sessionIdMatch = sessionUrl.match(/discovery\/([a-f0-9-]+)\/upload/);
    const sessionId = sessionIdMatch ? sessionIdMatch[1] : "unknown";

    await page.screenshot({ path: `${SCREENSHOT_DIR}/e2e-04-upload-page.png` });
    recordResult("Create Session", "pass", `Session created: ${sessionId}`, "e2e-04-upload-page.png");

    // ============================================================
    // STEP 4: Upload CSV File
    // ============================================================
    log("Step 4", "Uploading workforce CSV...");

    // Find file input and upload
    const fileInput = page.locator('input[type="file"]');
    await fileInput.setInputFiles(TEST_CSV);

    // Wait for upload to complete (look for row count)
    await page.waitForSelector('text=rows detected', { timeout: 15000 });

    await page.screenshot({ path: `${SCREENSHOT_DIR}/e2e-05-file-uploaded.png` });
    recordResult("Upload File", "pass", "File uploaded, rows detected", "e2e-05-file-uploaded.png");

    // ============================================================
    // STEP 5: Map Columns
    // ============================================================
    log("Step 5", "Mapping columns...");

    // Map Job Title -> Role
    const jobTitleSelect = page.locator('select').first();
    await jobTitleSelect.selectOption({ label: "Role (required)" });

    // Map Department -> Department (second select)
    const allSelects = page.locator('select');
    const selectCount = await allSelects.count();

    if (selectCount >= 2) {
      await allSelects.nth(1).selectOption({ label: "Department" });
    }
    if (selectCount >= 4) {
      await allSelects.nth(3).selectOption({ label: "Geography" });  // Location
    }
    if (selectCount >= 5) {
      await allSelects.nth(4).selectOption({ label: "Headcount" });  // Employee Count
    }

    await page.waitForTimeout(500);
    await page.screenshot({ path: `${SCREENSHOT_DIR}/e2e-06-columns-mapped.png` });
    recordResult("Map Columns", "pass", "Columns mapped: Role, Department, Geography, Headcount", "e2e-06-columns-mapped.png");

    // ============================================================
    // STEP 6: Proceed to Map Roles
    // ============================================================
    log("Step 6", "Proceeding to Map Roles step...");

    // Click Continue button
    await page.click('button:has-text("Continue")');

    // Wait for Map Roles page
    await page.waitForURL("**/map-roles", { timeout: 10000 });
    await waitForPageLoad(page);

    await page.screenshot({ path: `${SCREENSHOT_DIR}/e2e-07-map-roles.png` });
    recordResult("Proceed to Map Roles", "pass", "Reached Map Roles step", "e2e-07-map-roles.png");

    // ============================================================
    // TEST SUMMARY
    // ============================================================
    console.log("\n" + "=".repeat(60));
    console.log("TEST SUMMARY");
    console.log("=".repeat(60));

    const passed = results.filter(r => r.status === "pass").length;
    const failed = results.filter(r => r.status === "fail").length;

    console.log(`\nTotal: ${results.length} | Passed: ${passed} | Failed: ${failed}`);

    if (failed === 0) {
      console.log("\n🎉 ALL TESTS PASSED!\n");
    } else {
      console.log("\n⚠️  SOME TESTS FAILED\n");
      results.filter(r => r.status === "fail").forEach(r => {
        console.log(`  ❌ ${r.step}: ${r.message}`);
      });
    }

    console.log("Screenshots saved to:", SCREENSHOT_DIR);
    console.log("=".repeat(60) + "\n");

  } catch (error) {
    console.error("\n❌ Test failed with error:", error);
    await page.screenshot({ path: `${SCREENSHOT_DIR}/e2e-error.png` });
    console.log("Error screenshot saved to: e2e-error.png");
  } finally {
    await client.disconnect();
  }
}

// Run the test
runHappyPathTest().catch(console.error);
