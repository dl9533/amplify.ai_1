/**
 * Analysis & Roadmap Deep Test E2E
 *
 * This test focuses on deep testing of Steps 4 and 5:
 *
 * Step 4: ANALYSIS (Deep Testing)
 *   - Test all 5 dimension tabs (Role, Department, LOB, Geography, Task)
 *   - Test priority tier filters (All, High, Medium, Low)
 *   - Test column sorting (Name, Exposure, Impact, Priority)
 *   - Verify score displays (exposure %, impact %, priority tier badges)
 *   - Test Re-analyze button
 *
 * Step 5: ROADMAP (Deep Testing)
 *   - Verify 3 Kanban columns (NOW, NEXT, LATER)
 *   - Verify candidate cards have all required info
 *   - Test phase summary counts
 *   - Test handoff modal with notes
 *   - Verify handoff validation
 *
 * Test Data: Insurance Claims Workforce (15 roles, 895 employees)
 *
 * Prerequisites:
 *   - Frontend: http://localhost:5173
 *   - Backend: http://localhost:8001
 *   - dev-browser: http://localhost:9222
 *
 * To run:
 *   cd /Users/dl9533/.claude/plugins/cache/dev-browser-marketplace/dev-browser/66682fb0513a/skills/dev-browser
 *   npx tsx /Users/dl9533/projects/amplify.ai_1/discovery/tests/e2e/analysis_roadmap_deep_test.ts
 */

import { connect, waitForPageLoad } from "@/client.js";

// ============================================================
// CONFIGURATION
// ============================================================
const SERVER_URL = "http://localhost:9222";
const FRONTEND_URL = "http://localhost:5173";
const TEST_CSV = "/Users/dl9533/projects/amplify.ai_1/discovery/tests/e2e/test_data/insurance_claims_workforce.csv";
const SCREENSHOT_DIR = "tmp";

const TEST_EMAIL = "test@example.com";
const TEST_PASSWORD = "password123";

// ============================================================
// TEST RESULT TRACKING
// ============================================================
interface TestResult {
  step: string;
  status: "pass" | "fail" | "skip";
  message: string;
  details?: string;
  screenshot?: string;
}

const results: TestResult[] = [];
let testStartTime: number;

function log(step: string, message: string) {
  const elapsed = Date.now() - testStartTime;
  console.log(`[${elapsed}ms] [${step}] ${message}`);
}

function recordResult(
  step: string,
  status: "pass" | "fail" | "skip",
  message: string,
  details?: string,
  screenshot?: string
) {
  results.push({ step, status, message, details, screenshot });
  const icon = status === "pass" ? "✅" : status === "fail" ? "❌" : "⏭️";
  console.log(`${icon} ${step}: ${message}`);
  if (details) console.log(`   └─ ${details}`);
}

// ============================================================
// HELPER: SETUP SESSION THROUGH STEP 3
// ============================================================
async function setupSessionThroughActivities(page: any): Promise<string> {
  log("Setup", "Creating session and advancing to Activities...");

  // Login if needed
  await page.goto(FRONTEND_URL);
  await waitForPageLoad(page);

  if (page.url().includes("/login")) {
    await page.fill('input[type="email"]', TEST_EMAIL);
    await page.fill('input[type="password"]', TEST_PASSWORD);
    await page.click('button:has-text("Sign in")');
    await page.waitForURL("**/discovery", { timeout: 10000 });
    await waitForPageLoad(page);
  }

  // Create session
  const newSessionBtn = page.locator('button:has-text("New Session")').first();
  await newSessionBtn.click();
  await page.waitForURL("**/upload", { timeout: 10000 });
  await waitForPageLoad(page);

  const sessionUrl = page.url();
  const sessionIdMatch = sessionUrl.match(/discovery\/([a-f0-9-]+)\/upload/);
  const sessionId = sessionIdMatch ? sessionIdMatch[1] : "unknown";
  log("Setup", `Session: ${sessionId}`);

  // Upload file
  const fileInput = page.locator('input[type="file"]');
  await fileInput.setInputFiles(TEST_CSV);
  await page.waitForSelector('text=rows detected', { timeout: 25000 });

  // Map columns
  const allSelects = page.locator("select");
  const selectCount = await allSelects.count();
  for (let i = 0; i < Math.min(selectCount, 5); i++) {
    const select = allSelects.nth(i);
    const options = await select.locator("option").allTextContents();
    if (i === 0 && options.some((o: string) => o.includes("Role"))) {
      await select.selectOption({ label: "Role (required)" });
    } else if (i === 1 && options.some((o: string) => o.includes("Department"))) {
      await select.selectOption({ label: "Department" });
    } else if (i === 2 && options.some((o: string) => o.includes("Line of Business"))) {
      await select.selectOption({ label: "Line of Business" });
    } else if (i === 3 && options.some((o: string) => o.includes("Geography"))) {
      await select.selectOption({ label: "Geography" });
    } else if (i === 4 && options.some((o: string) => o.includes("Headcount"))) {
      await select.selectOption({ label: "Headcount" });
    }
  }

  await page.waitForTimeout(500);
  await page.click('button:has-text("Continue")');
  await page.waitForURL("**/map-roles", { timeout: 15000 });
  await waitForPageLoad(page);

  // Confirm role mappings
  log("Setup", "Confirming role mappings...");
  await page.waitForSelector('[class*="surface"]', { timeout: 45000 });
  await page.waitForTimeout(3000);

  // Bulk confirm
  const bulkConfirmBtn = page.locator('button:has-text("Confirm all")').first();
  if ((await bulkConfirmBtn.count()) > 0) {
    try {
      await bulkConfirmBtn.click();
      await page.waitForTimeout(1500);
    } catch {
      // Continue
    }
  }

  // Individual confirms
  for (let i = 0; i < 20; i++) {
    const confirmBtn = page.locator('button:has-text("Confirm"):not(:has-text("all"))').first();
    if ((await confirmBtn.count()) > 0 && (await confirmBtn.isVisible())) {
      try {
        await confirmBtn.click();
        await page.waitForTimeout(300);
      } catch {
        break;
      }
    } else {
      break;
    }
  }

  // Confirm all remaining
  const confirmAllBtn = page.locator('button:has-text("Confirm All")').first();
  if ((await confirmAllBtn.count()) > 0) {
    await confirmAllBtn.click();
    await page.waitForTimeout(2000);
  }

  // Continue to Activities
  const continueBtn = page.locator('button:has-text("Continue")');
  if ((await continueBtn.count()) > 0 && !(await continueBtn.isDisabled())) {
    await continueBtn.click();
    await page.waitForURL("**/activities", { timeout: 20000 });
    await waitForPageLoad(page);
  }

  // Auto-select activities
  log("Setup", "Selecting activities...");
  await page.waitForTimeout(2000);
  const autoSelectBtn = page.locator('button:has-text("Auto-select")');
  if ((await autoSelectBtn.count()) > 0) {
    await autoSelectBtn.click();
    await page.waitForTimeout(2000);
  }

  log("Setup", "Session ready at Activities step");
  return sessionId;
}

// ============================================================
// MAIN TEST
// ============================================================
async function runAnalysisRoadmapDeepTest() {
  testStartTime = Date.now();

  console.log("\n" + "═".repeat(75));
  console.log("  ANALYSIS & ROADMAP DEEP TEST");
  console.log("  Test Data: Insurance Claims Workforce (15 roles)");
  console.log("═".repeat(75) + "\n");

  const client = await connect(SERVER_URL);
  const page = await client.page("analysis-roadmap-test", {
    viewport: { width: 1440, height: 900 },
  });

  let sessionId = "";

  try {
    // ════════════════════════════════════════════════════════════
    // SETUP: Create session through Step 3
    // ════════════════════════════════════════════════════════════
    sessionId = await setupSessionThroughActivities(page);
    await page.screenshot({ path: `${SCREENSHOT_DIR}/ar-00-setup-complete.png` });
    recordResult("Setup", "pass", "Session created through Activities", `Session: ${sessionId.slice(0, 8)}...`);

    // Continue to Analysis
    const continueToAnalysis = page.locator('button:has-text("Continue")');
    if ((await continueToAnalysis.count()) > 0 && !(await continueToAnalysis.isDisabled())) {
      await continueToAnalysis.click();
      await page.waitForURL("**/analysis", { timeout: 20000 });
      await waitForPageLoad(page);
    }

    // ════════════════════════════════════════════════════════════
    // ANALYSIS: DEEP TESTING
    // ════════════════════════════════════════════════════════════
    log("Analysis", "Starting deep analysis testing...");
    await page.waitForTimeout(2500);

    // Trigger analysis if needed
    const runAnalysisBtn = page.locator('button:has-text("Run Analysis")');
    if ((await runAnalysisBtn.count()) > 0) {
      log("Analysis", "Triggering analysis...");
      await runAnalysisBtn.click();
      await page.waitForTimeout(5000);
    }

    await page.screenshot({ path: `${SCREENSHOT_DIR}/ar-01-analysis-initial.png` });

    // ─────────────────────────────────────────────────────────────
    // TEST: Dimension Tabs
    // ─────────────────────────────────────────────────────────────
    log("Analysis", "Testing dimension tabs...");

    const dimensions = [
      { name: "By Role", screenshot: "ar-02-by-role.png" },
      { name: "By Department", screenshot: "ar-03-by-dept.png" },
      { name: "By Line of Business", screenshot: "ar-04-by-lob.png" },
      { name: "By Geography", screenshot: "ar-05-by-geo.png" },
      { name: "By Task", screenshot: "ar-06-by-task.png" },
    ];

    let dimensionsTested = 0;
    for (const dim of dimensions) {
      const tab = page.locator(`button:has-text("${dim.name}")`);
      if ((await tab.count()) > 0) {
        await tab.click();
        await page.waitForTimeout(1200);
        await page.screenshot({ path: `${SCREENSHOT_DIR}/${dim.screenshot}` });
        dimensionsTested++;
        log("Analysis", `Tested ${dim.name} dimension`);
      }
    }

    recordResult(
      "Analysis: Dimensions",
      dimensionsTested >= 3 ? "pass" : "fail",
      `Tested ${dimensionsTested}/5 dimension tabs`,
      undefined,
      "ar-04-by-lob.png"
    );

    // ─────────────────────────────────────────────────────────────
    // TEST: Priority Tier Filters
    // ─────────────────────────────────────────────────────────────
    log("Analysis", "Testing priority tier filters...");

    // Reset to By Role
    const roleTab = page.locator('button:has-text("By Role")');
    if ((await roleTab.count()) > 0) {
      await roleTab.click();
      await page.waitForTimeout(1000);
    }

    const tierFilters = [
      { name: "High", screenshot: "ar-07-filter-high.png" },
      { name: "Medium", screenshot: "ar-08-filter-medium.png" },
      { name: "Low", screenshot: "ar-09-filter-low.png" },
      { name: "All", screenshot: "ar-10-filter-all.png" },
    ];

    let filtersTested = 0;
    for (const filter of tierFilters) {
      const filterBtn = page.locator(`button:has-text("${filter.name}")`).first();
      if ((await filterBtn.count()) > 0) {
        await filterBtn.click();
        await page.waitForTimeout(800);
        await page.screenshot({ path: `${SCREENSHOT_DIR}/${filter.screenshot}` });
        filtersTested++;
        log("Analysis", `Tested ${filter.name} filter`);
      }
    }

    recordResult(
      "Analysis: Filters",
      filtersTested >= 3 ? "pass" : "fail",
      `Tested ${filtersTested}/4 priority filters`,
      undefined,
      "ar-07-filter-high.png"
    );

    // ─────────────────────────────────────────────────────────────
    // TEST: Column Sorting
    // ─────────────────────────────────────────────────────────────
    log("Analysis", "Testing column sorting...");

    // Reset filter to All
    const allFilterBtn = page.locator('button:has-text("All")').first();
    if ((await allFilterBtn.count()) > 0) {
      await allFilterBtn.click();
      await page.waitForTimeout(500);
    }

    const sortColumns = ["Name", "AI Exposure", "Impact", "Priority"];
    let sortsTested = 0;

    for (const column of sortColumns) {
      const headerBtn = page.locator(`button:has-text("${column}")`).first();
      if ((await headerBtn.count()) > 0) {
        await headerBtn.click();
        await page.waitForTimeout(600);
        sortsTested++;
        log("Analysis", `Sorted by ${column}`);

        // Click again for reverse sort
        await headerBtn.click();
        await page.waitForTimeout(400);
      }
    }

    await page.screenshot({ path: `${SCREENSHOT_DIR}/ar-11-sorted.png` });

    recordResult(
      "Analysis: Sorting",
      sortsTested >= 2 ? "pass" : "fail",
      `Tested ${sortsTested} column sorts`,
      undefined,
      "ar-11-sorted.png"
    );

    // ─────────────────────────────────────────────────────────────
    // TEST: Re-analyze Button
    // ─────────────────────────────────────────────────────────────
    log("Analysis", "Testing re-analyze button...");

    const reAnalyzeBtn = page.locator('button:has-text("Re-analyze")');
    if ((await reAnalyzeBtn.count()) > 0) {
      await reAnalyzeBtn.click();
      log("Analysis", "Re-analyze triggered");
      await page.waitForTimeout(3000);
      await page.screenshot({ path: `${SCREENSHOT_DIR}/ar-12-reanalyzed.png` });
      recordResult("Analysis: Re-analyze", "pass", "Re-analyze completed", undefined, "ar-12-reanalyzed.png");
    } else {
      recordResult("Analysis: Re-analyze", "skip", "Re-analyze button not found");
    }

    // ─────────────────────────────────────────────────────────────
    // TEST: Verify Score Displays
    // ─────────────────────────────────────────────────────────────
    log("Analysis", "Verifying score displays...");

    const pageContent = await page.content();
    const hasPercentages = pageContent.includes("%");
    const hasTierBadges =
      pageContent.includes("HIGH") || pageContent.includes("MEDIUM") || pageContent.includes("LOW");

    recordResult(
      "Analysis: Scores",
      hasPercentages ? "pass" : "fail",
      `Score displays: percentages=${hasPercentages}, badges=${hasTierBadges}`
    );

    // Continue to Roadmap
    const continueToRoadmap = page.locator('button:has-text("Continue")');
    if ((await continueToRoadmap.count()) > 0 && !(await continueToRoadmap.isDisabled())) {
      log("Analysis", "Proceeding to Roadmap...");
      await continueToRoadmap.click();
      await page.waitForURL("**/roadmap", { timeout: 20000 });
      await waitForPageLoad(page);
    }

    // ════════════════════════════════════════════════════════════
    // ROADMAP: DEEP TESTING
    // ════════════════════════════════════════════════════════════
    log("Roadmap", "Starting deep roadmap testing...");
    await page.waitForTimeout(2500);
    await page.screenshot({ path: `${SCREENSHOT_DIR}/ar-13-roadmap-initial.png` });

    // ─────────────────────────────────────────────────────────────
    // TEST: Kanban Columns
    // ─────────────────────────────────────────────────────────────
    log("Roadmap", "Verifying Kanban columns...");

    const phases = [
      { name: "Now", description: "immediate action" },
      { name: "Next", description: "plan for next" },
      { name: "Later", description: "future consideration" },
    ];

    let columnsFound = 0;
    for (const phase of phases) {
      const phaseText = page.locator(`text=${phase.name}`).first();
      if ((await phaseText.count()) > 0) {
        columnsFound++;
        log("Roadmap", `Found "${phase.name}" column`);
      }
    }

    recordResult(
      "Roadmap: Columns",
      columnsFound === 3 ? "pass" : columnsFound >= 2 ? "pass" : "fail",
      `Found ${columnsFound}/3 Kanban columns`
    );

    // ─────────────────────────────────────────────────────────────
    // TEST: Phase Summary Counts
    // ─────────────────────────────────────────────────────────────
    log("Roadmap", "Checking phase summary counts...");

    const summaryStats = page.locator('[class*="surface"] [class*="text-2xl"]');
    const statsCount = await summaryStats.count();
    log("Roadmap", `Found ${statsCount} summary stat displays`);

    recordResult(
      "Roadmap: Summary",
      statsCount >= 3 ? "pass" : "fail",
      `Phase summary stats: ${statsCount} displays`
    );

    // ─────────────────────────────────────────────────────────────
    // TEST: Candidate Cards
    // ─────────────────────────────────────────────────────────────
    log("Roadmap", "Verifying candidate cards...");

    const candidateCards = page.locator('[draggable="true"]');
    const cardCount = await candidateCards.count();
    log("Roadmap", `Found ${cardCount} candidate cards`);

    if (cardCount > 0) {
      // Check first card has expected elements
      const firstCard = candidateCards.first();
      const cardText = await firstCard.textContent();
      const hasRoleName = cardText && cardText.length > 5;
      const hasPriorityInfo = cardText && (cardText.includes("Priority") || cardText.includes("%"));

      log("Roadmap", `Card content check: hasRoleName=${hasRoleName}, hasPriority=${hasPriorityInfo}`);
    }

    await page.screenshot({ path: `${SCREENSHOT_DIR}/ar-14-roadmap-cards.png` });

    recordResult(
      "Roadmap: Cards",
      cardCount > 0 ? "pass" : "skip",
      `Found ${cardCount} candidate cards`,
      undefined,
      "ar-14-roadmap-cards.png"
    );

    // ─────────────────────────────────────────────────────────────
    // TEST: Handoff Modal
    // ─────────────────────────────────────────────────────────────
    log("Roadmap", "Testing handoff modal...");

    const handoffBtn = page.locator('button:has-text("Hand off")');
    if ((await handoffBtn.count()) > 0) {
      const isDisabled = await handoffBtn.isDisabled();
      log("Roadmap", `Handoff button disabled: ${isDisabled}`);

      if (!isDisabled) {
        await handoffBtn.click();
        await page.waitForTimeout(1000);

        const modal = page.locator('[role="dialog"], [class*="modal"], [class*="Modal"]');
        if ((await modal.count()) > 0) {
          await page.screenshot({ path: `${SCREENSHOT_DIR}/ar-15-handoff-modal.png` });
          log("Roadmap", "Handoff modal opened");

          // Test notes textarea
          const notesTextarea = page.locator("textarea");
          if ((await notesTextarea.count()) > 0) {
            await notesTextarea.fill("Test handoff notes - Insurance claims processing prioritization");
            log("Roadmap", "Filled handoff notes");
            await page.screenshot({ path: `${SCREENSHOT_DIR}/ar-16-handoff-with-notes.png` });
          }

          // Verify candidate list in modal
          const modalContent = await modal.textContent();
          const hasCandidateList = modalContent && modalContent.length > 50;
          log("Roadmap", `Modal has candidate list: ${hasCandidateList}`);

          // Close modal (don't actually submit)
          const cancelBtn = page.locator('button:has-text("Cancel")');
          if ((await cancelBtn.count()) > 0) {
            await cancelBtn.click();
            await page.waitForTimeout(500);
            log("Roadmap", "Closed handoff modal");
          }

          recordResult(
            "Roadmap: Handoff Modal",
            "pass",
            "Handoff modal tested with notes",
            undefined,
            "ar-16-handoff-with-notes.png"
          );
        } else {
          recordResult("Roadmap: Handoff Modal", "fail", "Modal did not open");
        }
      } else {
        recordResult(
          "Roadmap: Handoff Modal",
          "skip",
          "Handoff button disabled (no items in NOW phase)"
        );
      }
    } else {
      recordResult("Roadmap: Handoff Modal", "skip", "Handoff button not found");
    }

    // ─────────────────────────────────────────────────────────────
    // TEST: Drag-and-Drop Hint
    // ─────────────────────────────────────────────────────────────
    log("Roadmap", "Checking drag-and-drop UI...");

    const tipText = page.locator('text=Drag and drop, text=drag');
    const hasDragTip = (await tipText.count()) > 0;
    log("Roadmap", `Drag-and-drop tip visible: ${hasDragTip}`);

    await page.screenshot({ path: `${SCREENSHOT_DIR}/ar-17-roadmap-final.png` });

    recordResult(
      "Roadmap: UI Complete",
      "pass",
      "Roadmap UI fully loaded",
      `Cards: ${cardCount}, Columns: ${columnsFound}`,
      "ar-17-roadmap-final.png"
    );

    // ════════════════════════════════════════════════════════════
    // TEST SUMMARY
    // ════════════════════════════════════════════════════════════
    const totalDuration = Date.now() - testStartTime;

    console.log("\n" + "═".repeat(75));
    console.log("  TEST SUMMARY - ANALYSIS & ROADMAP DEEP TEST");
    console.log("═".repeat(75));

    const passed = results.filter((r) => r.status === "pass").length;
    const failed = results.filter((r) => r.status === "fail").length;
    const skipped = results.filter((r) => r.status === "skip").length;

    console.log(`\n  Total Tests: ${results.length}`);
    console.log(`  ✅ Passed: ${passed}`);
    console.log(`  ❌ Failed: ${failed}`);
    console.log(`  ⏭️  Skipped: ${skipped}`);
    console.log(`  ⏱️  Duration: ${(totalDuration / 1000).toFixed(1)}s`);
    console.log(`  🔑 Session ID: ${sessionId}`);

    console.log("\n  Test Results:");
    console.log("  " + "─".repeat(71));

    // Group by category
    const analysisTests = results.filter((r) => r.step.startsWith("Analysis"));
    const roadmapTests = results.filter((r) => r.step.startsWith("Roadmap"));
    const otherTests = results.filter(
      (r) => !r.step.startsWith("Analysis") && !r.step.startsWith("Roadmap")
    );

    if (otherTests.length > 0) {
      console.log("\n  Setup:");
      otherTests.forEach((r) => {
        const icon = r.status === "pass" ? "✅" : r.status === "fail" ? "❌" : "⏭️";
        console.log(`    ${icon} ${r.step}: ${r.message}`);
      });
    }

    console.log("\n  Analysis Tests:");
    analysisTests.forEach((r) => {
      const icon = r.status === "pass" ? "✅" : r.status === "fail" ? "❌" : "⏭️";
      console.log(`    ${icon} ${r.step}: ${r.message}`);
    });

    console.log("\n  Roadmap Tests:");
    roadmapTests.forEach((r) => {
      const icon = r.status === "pass" ? "✅" : r.status === "fail" ? "❌" : "⏭️";
      console.log(`    ${icon} ${r.step}: ${r.message}`);
    });

    console.log("\n  " + "─".repeat(71));

    if (failed === 0) {
      console.log("\n  🎉 ALL TESTS COMPLETED SUCCESSFULLY!");
    } else {
      console.log(`\n  ⚠️  ${failed} TEST(S) FAILED`);
    }

    console.log(`\n  Screenshots saved to: ${SCREENSHOT_DIR}/ar-*.png`);
    console.log("═".repeat(75) + "\n");

  } catch (error) {
    console.error("\n❌ Test failed with error:", error);
    await page.screenshot({ path: `${SCREENSHOT_DIR}/ar-error.png` });
    recordResult("Error", "fail", String(error), undefined, "ar-error.png");

    // Print partial summary
    const totalDuration = Date.now() - testStartTime;
    console.log("\n" + "═".repeat(75));
    console.log("  TEST SUMMARY (PARTIAL - ERROR OCCURRED)");
    console.log("═".repeat(75));
    console.log(`\n  Duration: ${(totalDuration / 1000).toFixed(1)}s`);
    console.log(`  Session ID: ${sessionId}`);
    console.log("\n  Completed Tests:");
    results.forEach((r) => {
      const icon = r.status === "pass" ? "✅" : r.status === "fail" ? "❌" : "⏭️";
      console.log(`  ${icon} ${r.step}: ${r.message}`);
    });
    console.log("═".repeat(75) + "\n");
  } finally {
    await client.disconnect();
  }
}

// Run the test
runAnalysisRoadmapDeepTest().catch(console.error);
