import {
  compareRunsResponse,
  historyItem,
  historyListResponse,
  recentCompareSet,
  recentCompareSetsResponse
} from "./support/fixtures";
import { expect, test } from "./support/testHarness";

test.describe("history and compare smoke flows", () => {
  test("renders degraded history data and navigates into compare successfully", async ({
    apiMock,
    page
  }) => {
    let recentCompares = recentCompareSetsResponse([]);
    apiMock.onJson(
      "GET",
      "/history/runs?limit=50&offset=0&sort=started_desc",
      historyListResponse(
        [
          historyItem({
            run_id: "strategy-run-001",
            run_name: "trend-a",
            instrument_symbol: "AAPL",
            has_strategy: true,
            detail_available: false
          }),
          historyItem({
            run_id: "strategy-run-002",
            run_name: "trend-b",
            instrument_symbol: "AAPL",
            has_strategy: true
          })
        ],
        ["Recovered one manifest from normalized summary data."]
      )
    );
    apiMock.on("GET", "/workflow/recent-compares?limit=20", () => ({ body: recentCompares }));
    apiMock.onJson("POST", "/compare/runs", compareRunsResponse());
    apiMock.on("POST", "/workflow/recent-compares/touch", () => {
      recentCompares = recentCompareSetsResponse([
        recentCompareSet({
          id: "cmp_001",
          compare_mode: "auto",
          run_ids: ["strategy-run-001", "strategy-run-002"],
          fingerprint: "fp-001"
        })
      ]);
      return { body: recentCompares.items[0] };
    });

    await page.goto("/history");

    await expect(page.getByRole("heading", { name: "Run History" }).first()).toBeVisible();
    await expect(page.getByText("Recovered one manifest from normalized summary data.")).toBeVisible();
    await expect(page.getByText("strategy-run-001")).toBeVisible();
    await expect(page.getByText("strategy-run-002")).toBeVisible();

    const compareButton = page.getByRole("button", { name: "Compare Selected (0)" });
    await expect(compareButton).toBeDisabled();

    await page.getByLabel("Select run strategy-run-001").check();
    await page.getByLabel("Select run strategy-run-002").check();

    await expect(page.getByRole("button", { name: "Compare Selected (2)" })).toBeEnabled();
    await page.getByRole("button", { name: "Compare Selected (2)" }).click();

    await expect(page).toHaveURL(/\/compare\?ids=.*strategy-run-001.*strategy-run-002.*mode=auto/);
    await expect(page.getByRole("heading", { name: "Compare Highlights" })).toBeVisible();
    await expect(page.getByText("Using normalized summary metrics for compare rows.")).toBeVisible();
    await expect(page.getByText("Total Return %")).toBeVisible();
    await expect(page.getByText("trend-a")).toBeVisible();
    await expect(page.getByRole("heading", { name: "Recent Compares" })).toBeVisible();
    await expect(page.getByText("strategy-run-001, strategy-run-002")).toBeVisible();
    apiMock.assertCalled("POST /compare/runs");
  });

  test("renders the empty history state", async ({ apiMock, page }) => {
    apiMock.onJson(
      "GET",
      "/history/runs?limit=50&offset=0&sort=started_desc",
      historyListResponse([])
    );

    await page.goto("/history");

    await expect(page.getByText("No saved runs matched your filters.")).toBeVisible();
  });

  test("renders the compare page empty state before any selection", async ({
    apiMock,
    page
  }) => {
    apiMock.onJson("GET", "/workflow/recent-compares?limit=20", recentCompareSetsResponse([]));

    await page.goto("/compare");

    await expect(page.getByRole("heading", { name: "Compare Runs" })).toBeVisible();
    await expect(page.getByLabel("Run IDs (CSV)")).toBeVisible();
    await expect(page.getByLabel("Compare mode")).toBeVisible();
    await expect(page.getByText("Select at least two run IDs to compare.")).toBeVisible();
  });

  test("reuses a recent compare selection", async ({ apiMock, page }) => {
    apiMock.onJson(
      "GET",
      "/workflow/recent-compares?limit=20",
      recentCompareSetsResponse([
        recentCompareSet({
          id: "cmp_001",
          compare_mode: "strategy",
          run_ids: ["strategy-run-003", "strategy-run-004"],
          fingerprint: "fp-003-004"
        })
      ])
    );
    apiMock.onJson("POST", "/compare/runs", compareRunsResponse());
    apiMock.onJson(
      "POST",
      "/workflow/recent-compares/touch",
      recentCompareSet({
        id: "cmp_001",
        compare_mode: "strategy",
        run_ids: ["strategy-run-003", "strategy-run-004"],
        fingerprint: "fp-003-004"
      })
    );

    await page.goto("/compare");

    await page.getByRole("button", { name: "Reuse Selection" }).click();

    await expect(page).toHaveURL(/ids=strategy-run-003%2Cstrategy-run-004&mode=strategy/);
    await expect(page.getByText("trend-a")).toBeVisible();
  });

  test("renders incompatible compare errors", async ({ apiMock, page }) => {
    apiMock.onJson("GET", "/workflow/recent-compares?limit=20", recentCompareSetsResponse([]));
    apiMock.onError(
      "POST",
      "/compare/runs",
      409,
      "incompatible_runs",
      "Selected runs are not compatible for compare."
    );

    await page.goto("/compare?ids=strategy-run-001,strategy-run-003&mode=auto");

    await expect(page.getByRole("alert")).toContainText("API Error: incompatible_runs");
    await expect(page.getByRole("alert")).toContainText(
      "Selected runs are not compatible for compare."
    );
  });
});
