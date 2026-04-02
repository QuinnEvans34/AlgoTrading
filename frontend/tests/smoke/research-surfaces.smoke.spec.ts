import {
  assetResearchMemoResponse,
  assetResearchQuestionResponse,
  capabilitiesResponse,
  healthResponse,
  historyItem,
  historyListResponse,
  marketDataPreviewResponse,
  recentAsset,
  recentAssetsResponse,
  recentCompareSet,
  recentCompareSetsResponse,
  savedConfigListResponse,
  savedConfigSummary,
  watchlistItem,
  watchlistResponse
} from "./support/fixtures";
import { expect, test } from "./support/testHarness";

test.describe("research product alignment smoke flows", () => {
  test("renders the dashboard with persisted workflow continuity", async ({
    apiMock,
    page
  }) => {
    apiMock.onJson("GET", "/health", healthResponse());
    apiMock.onJson("GET", "/metadata/capabilities", capabilitiesResponse());
    apiMock.onJson(
      "GET",
      "/workflow/watchlist?limit=100",
      watchlistResponse([
        watchlistItem({ id: "wl_001", symbol: "AAPL", asset_class: "stock" }),
        watchlistItem({ id: "wl_002", symbol: "EUR_USD", asset_class: "forex" })
      ])
    );
    apiMock.onJson(
      "GET",
      "/workflow/recent-assets?limit=20",
      recentAssetsResponse([
        recentAsset({ id: "ra_001", symbol: "MSFT", asset_class: "stock" }),
        recentAsset({ id: "ra_002", symbol: "USD_JPY", asset_class: "forex" })
      ])
    );
    apiMock.onJson(
      "GET",
      "/workflow/saved-configs?config_type=strategy&limit=4",
      savedConfigListResponse([
        savedConfigSummary({
          id: "strategy_cfg_010",
          config_type: "strategy",
          name: "trend-template",
          instrument_symbol: "AAPL"
        })
      ])
    );
    apiMock.onJson(
      "GET",
      "/workflow/saved-configs?config_type=ml&limit=4",
      savedConfigListResponse([
        savedConfigSummary({
          id: "ml_cfg_010",
          config_type: "ml",
          name: "ml-template",
          instrument_symbol: "EUR_USD",
          asset_class: "forex"
        })
      ])
    );
    apiMock.onJson(
      "GET",
      "/workflow/recent-compares?limit=5",
      recentCompareSetsResponse([
        recentCompareSet({
          id: "cmp_001",
          compare_mode: "strategy",
          run_ids: ["strategy-run-001", "strategy-run-002"],
          fingerprint: "cmp-001"
        })
      ])
    );
    apiMock.onJson(
      "GET",
      "/history/runs?limit=6&offset=0&sort=started_desc",
      historyListResponse([
        historyItem({
          run_id: "strategy-run-001",
          run_name: "trend-aapl",
          instrument_symbol: "AAPL"
        }),
        historyItem({
          run_id: "ml-run-002",
          run_name: "macro-eurusd",
          workflow_type: "ml_research",
          instrument_symbol: "EUR_USD",
          asset_class: "forex",
          has_strategy: false,
          has_ml: true
        })
      ])
    );

    await page.goto("/");

    await expect(page.getByRole("heading", { name: "Dashboard" })).toBeVisible();
    await expect(page.getByRole("heading", { name: "Watchlist" })).toBeVisible();
    await expect(page.getByRole("heading", { name: "AAPL" })).toBeVisible();
    await expect(page.getByRole("heading", { name: "EUR_USD" })).toBeVisible();
    await expect(page.getByRole("heading", { name: "Recent Assets" })).toBeVisible();
    await expect(page.getByText("MSFT")).toBeVisible();
    await expect(page.getByRole("heading", { name: "Saved Config Snapshot" })).toBeVisible();
    await expect(page.getByText("trend-template")).toBeVisible();
    await expect(page.getByRole("heading", { name: "System Status" })).toBeVisible();
  });

  test("supports stocks explorer watchlist flow and asset detail research flow", async ({
    apiMock,
    page
  }) => {
    const watchlist = [
      watchlistItem({ id: "wl_001", symbol: "MSFT", asset_class: "stock" })
    ];
    const recents = [
      recentAsset({ id: "ra_001", symbol: "TSLA", asset_class: "stock" })
    ];

    apiMock.on("GET", "/workflow/watchlist?limit=100", () => ({
      body: watchlistResponse(watchlist)
    }));
    apiMock.on("GET", "/workflow/recent-assets?limit=20", () => ({
      body: recentAssetsResponse(recents)
    }));
    apiMock.on("POST", "/workflow/watchlist/items", (request) => {
      const body = request.body as { symbol: string; asset_class: "stock" | "forex" };
      watchlist.unshift(
        watchlistItem({
          id: `wl_${watchlist.length + 1}`,
          symbol: body.symbol,
          asset_class: body.asset_class
        })
      );
      return { body: watchlist[0] };
    });
    apiMock.on("POST", "/workflow/recent-assets/touch", (request) => {
      const body = request.body as { symbol: string; asset_class: "stock" | "forex" };
      recents.splice(
        0,
        0,
        recentAsset({
          id: `ra_${recents.length + 1}`,
          symbol: body.symbol,
          asset_class: body.asset_class
        })
      );
      return { body: recents[0] };
    });
    apiMock.onJson("GET", "/metadata/capabilities", capabilitiesResponse());
    apiMock.onJson(
      "GET",
      "/workflow/saved-configs?config_type=strategy&limit=100",
      savedConfigListResponse([
        savedConfigSummary({
          id: "strategy_cfg_001",
          config_type: "strategy",
          name: "apple-trend",
          instrument_symbol: "AAPL"
        })
      ])
    );
    apiMock.onJson(
      "GET",
      "/workflow/saved-configs?config_type=ml&limit=100",
      savedConfigListResponse([
        savedConfigSummary({
          id: "ml_cfg_001",
          config_type: "ml",
          name: "apple-ml",
          instrument_symbol: "AAPL"
        })
      ])
    );
    apiMock.onJson(
      "GET",
      "/history/runs?q=AAPL&limit=12&offset=0&sort=started_desc",
      historyListResponse([
        historyItem({
          run_id: "strategy-run-001",
          run_name: "trend-aapl-a",
          instrument_symbol: "AAPL"
        }),
        historyItem({
          run_id: "strategy-run-002",
          run_name: "trend-aapl-b",
          instrument_symbol: "AAPL"
        }),
        historyItem({
          run_id: "ml-run-003",
          run_name: "ml-aapl-c",
          workflow_type: "ml_research",
          instrument_symbol: "AAPL",
          has_strategy: false,
          has_ml: true
        })
      ])
    );
    apiMock.onJson(
      "POST",
      "/market-data/historical-preview",
      marketDataPreviewResponse("AAPL", "stock")
    );
    apiMock.onJson(
      "POST",
      "/asset-research/memos",
      assetResearchMemoResponse("AAPL", "stock", {
        asset: {
          symbol: "AAPL",
          asset_class: "stock",
          name: "Apple"
        }
      })
    );
    apiMock.onJson(
      "POST",
      "/asset-research/questions",
      assetResearchQuestionResponse(
        "AAPL",
        "stock",
        "What changed in the latest filing?",
        {
          asset: {
            symbol: "AAPL",
            asset_class: "stock",
            name: "Apple"
          }
        }
      )
    );

    await page.goto("/stocks");

    await expect(page.getByRole("heading", { name: "Stocks Explorer" })).toBeVisible();
    await page.getByLabel("Search stocks").fill("Apple");
    await page.getByRole("button", { name: "Watchlist" }).first().click();
    await expect(page.getByRole("button", { name: "Remove" }).first()).toBeVisible();

    await page.getByRole("link", { name: "Open Detail" }).first().click();

    await expect(page).toHaveURL(/\/assets\/stock\/AAPL/);
    await expect(page.getByRole("heading", { name: /AAPL/ })).toBeVisible();
    await page.getByRole("tab", { name: "AI" }).click();
    await page.getByRole("button", { name: "Generate Research Memo" }).click();
    await expect(page.getByRole("heading", { name: "Grounded AI Research" })).toBeVisible();
    await expect(page.getByRole("heading", { name: "Overview" })).toBeVisible();
    await expect(page.getByText("Grounded overview.")).toBeVisible();
    await page
      .getByLabel("Grounded research question")
      .fill("What changed in the latest filing?");
    await page.getByRole("button", { name: "Ask Question" }).click();
    await expect(page.getByRole("heading", { name: "Answer" })).toBeVisible();
    await expect(page.getByText("Grounded answer.")).toBeVisible();
    await expect(page.getByRole("heading", { name: "Related Runs" })).toBeVisible();
    await expect(page.getByText("trend-aapl-a")).toBeVisible();
    await expect(page.getByRole("link", { name: "Compare the latest strategy runs" })).toBeVisible();

    await page.getByRole("tab", { name: "Performance" }).click();
    await expect(page.getByRole("heading", { name: "Performance Snapshot" })).toBeVisible();
    await expect(page.getByRole("img", { name: "AAPL Performance Preview chart" })).toBeVisible();
  });

  test("supports forex detail handoff into Strategy Lab and unavailable preview handling", async ({
    apiMock,
    page
  }) => {
    const watchlist = [
      watchlistItem({ id: "wl_fx_001", symbol: "EUR_USD", asset_class: "forex" })
    ];
    const recents = [
      recentAsset({ id: "ra_fx_001", symbol: "GBP_USD", asset_class: "forex" })
    ];

    apiMock.on("GET", "/workflow/watchlist?limit=100", () => ({
      body: watchlistResponse(watchlist)
    }));
    apiMock.on("GET", "/workflow/recent-assets?limit=20", () => ({
      body: recentAssetsResponse(recents)
    }));
    apiMock.on("POST", "/workflow/recent-assets/touch", (request) => {
      const body = request.body as { symbol: string; asset_class: "stock" | "forex" };
      recents.splice(
        0,
        0,
        recentAsset({
          id: `ra_fx_${recents.length + 1}`,
          symbol: body.symbol,
          asset_class: body.asset_class
        })
      );
      return { body: recents[0] };
    });
    apiMock.onJson("GET", "/metadata/capabilities", capabilitiesResponse());
    apiMock.onJson(
      "GET",
      "/workflow/saved-configs?config_type=strategy&limit=100",
      savedConfigListResponse([
        savedConfigSummary({
          id: "strategy_cfg_fx_001",
          config_type: "strategy",
          name: "eurusd-trend",
          instrument_symbol: "EUR_USD",
          asset_class: "forex"
        })
      ])
    );
    apiMock.onJson(
      "GET",
      "/workflow/saved-configs?config_type=ml&limit=100",
      savedConfigListResponse([
        savedConfigSummary({
          id: "ml_cfg_fx_001",
          config_type: "ml",
          name: "eurusd-ml",
          instrument_symbol: "EUR_USD",
          asset_class: "forex"
        })
      ])
    );
    apiMock.onJson(
      "GET",
      "/history/runs?q=EUR_USD&limit=12&offset=0&sort=started_desc",
      historyListResponse([])
    );
    apiMock.onError(
      "POST",
      "/market-data/historical-preview",
      422,
      "provider_not_supported",
      "Historical preview is not supported for this asset."
    );
    apiMock.onJson(
      "POST",
      "/asset-research/memos",
      assetResearchMemoResponse("EUR_USD", "forex", {
        asset: {
          symbol: "EUR_USD",
          asset_class: "forex",
          name: "Euro / US Dollar"
        },
        warnings: [
          "Provider-backed FX price preview is not currently available, so the memo is narrowed to catalog and workflow context."
        ]
      })
    );
    apiMock.onError(
      "POST",
      "/asset-research/questions",
      502,
      "asset_research_provider_error",
      "Upstream provider request failed."
    );

    await page.goto("/assets/forex/EUR_USD");

    await expect(page.getByRole("heading", { name: /EUR_USD/ })).toBeVisible();
    await page.getByRole("tab", { name: "Performance" }).click();
    await expect(
      page.getByText(
        "Historical preview is not currently available for this asset via the configured provider path."
      )
    ).toBeVisible();

    await page.getByRole("tab", { name: "AI" }).click();
    await page.getByRole("button", { name: "Generate Research Memo" }).click();
    await expect(page.getByText("Grounded FX performance context.")).toBeVisible();
    await expect(
      page.getByText(
        "Provider-backed FX price preview is not currently available, so the memo is narrowed to catalog and workflow context."
      )
    ).toBeVisible();
    await page.getByLabel("Grounded research question").fill("Why is this pair strong?");
    await page.getByRole("button", { name: "Ask Question" }).click();
    await expect(page.getByText("Upstream provider request failed.")).toBeVisible();

    await page.getByRole("link", { name: "Open Strategy Lab" }).click();

    await expect(page).toHaveURL(/\/strategy\?symbol=EUR_USD&assetClass=forex&interval=4h/);
    await expect(page.getByRole("heading", { name: "Strategy Research Run" })).toBeVisible();
    await expect(page.getByLabel("Symbol")).toHaveValue("EUR_USD");
    await expect(page.getByLabel("Asset Class")).toHaveValue("forex");
  });
});
