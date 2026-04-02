import {
  capabilitiesResponse,
  mlRunSummaryResponse,
  mlSavedConfig,
  recentAsset,
  recentAssetsResponse,
  savedConfigListResponse,
  savedConfigSummary,
  strategyRunSummaryResponse,
  strategySavedConfig,
  watchlistItem,
  watchlistResponse
} from "./support/fixtures";
import { expect, test } from "./support/testHarness";

function installResearchWorkflowMocks(apiMock: any, configType: "strategy" | "ml") {
  const configs =
    configType === "strategy"
      ? [savedConfigSummary({ id: "strategy_cfg_001", config_type: "strategy", name: "trend-template", instrument_symbol: "MSFT" })]
      : [savedConfigSummary({ id: "ml_cfg_001", config_type: "ml", name: "ml-template", instrument_symbol: "NVDA" })];
  const watchlist = [
    watchlistItem({ id: "wl_001", symbol: "AAPL", asset_class: "stock" })
  ];
  const recentAssets = [
    recentAsset({ id: "ra_001", symbol: "TSLA", asset_class: "stock" })
  ];

  apiMock.on("GET", `/workflow/saved-configs?config_type=${configType}&limit=100`, () =>
    ({ body: savedConfigListResponse(configs) })
  );
  apiMock.on("GET", "/workflow/watchlist?limit=100", () => ({
    body: watchlistResponse(watchlist)
  }));
  apiMock.on("GET", "/workflow/recent-assets?limit=20", () => ({
    body: recentAssetsResponse(recentAssets)
  }));

  apiMock.on("GET", /\/workflow\/saved-configs\/.+$/, () => ({
    body: configType === "strategy" ? strategySavedConfig() : mlSavedConfig()
  }));

  apiMock.on("POST", "/workflow/saved-configs", (request: any) => {
    const body = request.body as {
      config_type: "strategy" | "ml";
      name: string;
      description?: string | null;
    };
    const summary = savedConfigSummary({
      id: body.config_type === "strategy" ? "strategy_cfg_002" : "ml_cfg_002",
      config_type: body.config_type,
      name: body.name,
      description: body.description ?? null,
      instrument_symbol: body.config_type === "strategy" ? "MSFT" : "NVDA"
    });
    configs.unshift(summary);
    return {
      body:
        body.config_type === "strategy"
          ? strategySavedConfig({ ...summary })
          : mlSavedConfig({ ...summary })
    };
  });

  apiMock.on("PUT", /\/workflow\/saved-configs\/.+$/, (request: any) => {
    const body = request.body as {
      config_type: "strategy" | "ml";
      name: string;
      description?: string | null;
    };
    configs[0] = {
      ...configs[0],
      name: body.name,
      description: body.description ?? null
    };
    return {
      body:
        body.config_type === "strategy"
          ? strategySavedConfig({ ...configs[0] })
          : mlSavedConfig({ ...configs[0] })
    };
  });

  apiMock.on("DELETE", /\/workflow\/saved-configs\/.+$/, () => ({
    body: { deleted: true }
  }));

  apiMock.on("POST", "/workflow/watchlist/items", (request: any) => {
    const body = request.body as { symbol: string; asset_class: string; source_context?: string };
    const item = watchlistItem({
      id: "wl_002",
      symbol: body.symbol,
      asset_class: body.asset_class,
      source_context: body.source_context ?? null
    });
    watchlist.unshift(item);
    return { body: item };
  });

  apiMock.on("DELETE", /\/workflow\/watchlist\/items\/[^/]+\/[^/]+$/, () => {
    watchlist.splice(0, watchlist.length, ...watchlist.filter((item) => item.symbol !== "MSFT"));
    return { body: { deleted: true } };
  });

  apiMock.on("POST", "/workflow/recent-assets/touch", (request: any) => {
    const body = request.body as { symbol: string; asset_class: string; source_context?: string };
    const item = recentAsset({
      id: "ra_002",
      symbol: body.symbol,
      asset_class: body.asset_class,
      source_context: body.source_context ?? null
    });
    recentAssets.unshift(item);
    return { body: item };
  });
}

test.describe("research smoke flows", () => {
  test("loads the strategy page and renders a successful run result", async ({
    apiMock,
    page
  }) => {
    apiMock.onJson("GET", "/metadata/capabilities", capabilitiesResponse());
    installResearchWorkflowMocks(apiMock, "strategy");
    apiMock.onJson(
      "POST",
      "/research/strategy-runs",
      strategyRunSummaryResponse()
    );

    await page.goto("/strategy");

    await expect(
      page.getByRole("heading", { name: "Strategy Research Run" })
    ).toBeVisible();
    await expect(page.getByRole("heading", { name: "Strategy Config Library" })).toBeVisible();
    await expect(page.getByLabel("Symbol")).toBeVisible();
    await expect(page.getByLabel("Mode")).toBeVisible();
    await expect(page.getByLabel("Warmup bars")).toBeVisible();

    await page.getByLabel("Symbol").fill("MSFT");
    await page.getByLabel("Run name (optional)").fill("strategy-msft-v1");
    await page.getByRole("button", { name: "Run Strategy Research" }).click();

    await expect(page.getByRole("heading", { name: "Next Step" })).toBeVisible();
    await expect(
      page.getByRole("link", { name: "Open Strategy Detail Page" })
    ).toHaveAttribute("href", "/runs/strategy-run-001/strategy");
    await expect(page.getByText("technical_rule_v1")).toBeVisible();
    await expect(page.getByRole("heading", { name: "Step Timeline" })).toBeVisible();
    await expect(page.getByText("run_strategy_backtest")).toBeVisible();
    apiMock.assertCalled("POST /research/strategy-runs");
  });

  test("can save/load a strategy config and manage the watchlist", async ({
    apiMock,
    page
  }) => {
    apiMock.onJson("GET", "/metadata/capabilities", capabilitiesResponse());
    installResearchWorkflowMocks(apiMock, "strategy");

    await page.goto("/strategy");

    await page.getByLabel("Strategy Config Library name").fill("alpha-template");
    await page.getByRole("button", { name: "Save As New" }).click();
    await expect(page.getByText("Loaded config: strategy_cfg_002")).toBeVisible();
    await expect(page.getByText("alpha-template")).toBeVisible();

    await page.getByLabel("Symbol").fill("MSFT");
    await page.getByRole("button", { name: "Add Current Asset" }).click();
    await expect(page.getByRole("button", { name: "Remove Current Asset" })).toBeVisible();
    await page.getByRole("button", { name: "Remove Current Asset" }).click();

    await page.getByLabel("Symbol").fill("ZZZZ");
    await page.getByRole("button", { name: "Use" }).first().click();
    await expect(page.getByLabel("Symbol")).toHaveValue("AAPL");
  });

  test("renders strategy API failures without breaking the page", async ({
    apiMock,
    page
  }) => {
    apiMock.onJson("GET", "/metadata/capabilities", capabilitiesResponse());
    installResearchWorkflowMocks(apiMock, "strategy");
    apiMock.onError(
      "POST",
      "/research/strategy-runs",
      422,
      "invalid_strategy_request",
      "Strategy request validation failed."
    );

    await page.goto("/strategy");
    await page.getByRole("button", { name: "Run Strategy Research" }).click();

    await expect(page.getByRole("alert")).toContainText(
      "API Error: invalid_strategy_request"
    );
    await expect(page.getByRole("alert")).toContainText(
      "Strategy request validation failed."
    );
  });

  test("loads the ML page, saves a config, and renders a successful run result", async ({
    apiMock,
    page
  }) => {
    apiMock.onJson("GET", "/metadata/capabilities", capabilitiesResponse());
    installResearchWorkflowMocks(apiMock, "ml");
    apiMock.onJson("POST", "/research/ml-runs", mlRunSummaryResponse());

    await page.goto("/ml");

    await expect(page.getByRole("heading", { name: "ML Research Run" })).toBeVisible();
    await expect(page.getByRole("heading", { name: "ML Config Library" })).toBeVisible();
    await expect(page.getByLabel("Task Type")).toBeVisible();
    await expect(page.getByLabel("Horizon Bars")).toBeVisible();

    await page.getByLabel("ML Config Library name").fill("ml-template-two");
    await page.getByRole("button", { name: "Save As New" }).click();
    await expect(page.getByText("Loaded config: ml_cfg_002")).toBeVisible();

    await page.getByLabel("Task Type").selectOption("regression");
    await page.getByLabel("Horizon Bars").fill("8");
    await page.getByRole("button", { name: "Run ML Research" }).click();

    await expect(page.getByRole("heading", { name: "Next Step" })).toBeVisible();
    await expect(page.getByRole("link", { name: "Open ML Detail Page" })).toHaveAttribute(
      "href",
      "/runs/ml-run-001/ml"
    );
    await expect(page.getByRole("heading", { name: "ML Summary" })).toBeVisible();
    await expect(page.getByText("dummy_cls")).toBeVisible();
    await expect(page.getByText("accuracy")).toBeVisible();
    apiMock.assertCalled("POST /research/ml-runs");
  });

  test("renders ML API failures without breaking the page", async ({
    apiMock,
    page
  }) => {
    apiMock.onJson("GET", "/metadata/capabilities", capabilitiesResponse());
    installResearchWorkflowMocks(apiMock, "ml");
    apiMock.onError(
      "POST",
      "/research/ml-runs",
      422,
      "invalid_ml_request",
      "ML request validation failed."
    );

    await page.goto("/ml");
    await page.getByRole("button", { name: "Run ML Research" }).click();

    await expect(page.getByRole("alert")).toContainText("API Error: invalid_ml_request");
    await expect(page.getByRole("alert")).toContainText("ML request validation failed.");
  });
});
