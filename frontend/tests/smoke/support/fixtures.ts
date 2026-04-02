import type {
  AskAssetResearchQuestionResponse,
  GenerateAssetMemoResponse,
  CapabilitiesResponse,
  RunSummaryResponse,
  StepResult
} from "../../../src/lib/api/types";
import type { CompareRunsResponse, RunHistoryItem, RunHistoryListResponse } from "../../../src/lib/history/types";
import type {
  LiveExecutionAttemptsResponse,
  LiveExecutionReadinessResponse,
  LiveIntentValidationResponse,
  ManualLiveSubmitResponse
} from "../../../src/lib/liveExecution/types";
import type { PaperStateResponse } from "../../../src/lib/paperTrading/types";
import type { SystemSettingsResponse } from "../../../src/lib/settings/types";
import type {
  RecentAsset,
  RecentCompareSet,
  SavedResearchConfig,
  SavedResearchConfigListResponse,
  SavedResearchConfigSummary,
  WatchlistItem,
  WatchlistResponse,
  RecentAssetListResponse,
  RecentCompareSetListResponse
} from "../../../src/lib/workflow/types";

const BASE_TIME = "2026-03-26T12:00:00.000Z";

function stepResult(stepName: string, durationMs: number): StepResult {
  return {
    step_name: stepName,
    status: "success",
    started_at: BASE_TIME,
    ended_at: BASE_TIME,
    duration_ms: durationMs,
    error_type: null,
    error_message: null,
    metadata: {}
  };
}

export function capabilitiesResponse(): CapabilitiesResponse {
  return {
    workflows: ["strategy_research", "ml_research", "hybrid_research"],
    strategies: ["technical_rule_v1"],
    providers: ["oanda", "demo-feed"],
    intervals: ["1m", "5m", "1h", "1d"],
    asset_classes: ["stock", "forex"],
    model_families: ["dummy_classifier", "dummy_regressor"],
    feature_flags: {
      research_api_enabled: true,
      history_api_enabled: true,
      compare_api_enabled: true,
      paper_trading_enabled: true,
      live_execution_status_enabled: true,
      live_execution_submit_enabled: true
    },
    paper_trading: {
      supported_order_types: ["market", "limit"],
      supported_order_sides: ["buy", "sell"],
      supports_short: true,
      supports_signal_intents: true,
      supported_asset_classes: ["stock", "forex"]
    },
    live_execution: {
      broker_name: "oanda_stub",
      enabled: false,
      submission_allowed: false,
      configured: false,
      state: "disabled",
      message: "Live execution is guarded.",
      supported_order_types: ["market", "limit"],
      supported_order_sides: ["buy", "sell"],
      supported_asset_classes: ["stock", "forex"],
      supports_short: false,
      supports_cancel: false,
      supports_submit: true
    }
  };
}

export function healthResponse() {
  return {
    status: "ok",
    service: "capstone-api",
    version: "0.1.0",
    timestamp: BASE_TIME
  };
}

export function strategyRunSummaryResponse(): RunSummaryResponse {
  return {
    run_id: "strategy-run-001",
    run_name: "strategy-msft-v1",
    workflow_type: "strategy_research",
    status: "success",
    started_at: BASE_TIME,
    ended_at: BASE_TIME,
    duration_ms: 3210,
    instrument: {
      symbol: "MSFT",
      asset_class: "stock"
    },
    interval: "1d",
    candle_count: 220,
    candle_source_type: "inline_candles",
    step_results: [
      stepResult("load_candles", 25),
      stepResult("run_strategy_backtest", 260),
      stepResult("persist_artifacts", 15)
    ],
    metadata: {
      persisted: true
    },
    candle_time_range: {
      start: "2026-01-01T00:00:00.000Z",
      end: "2026-03-26T00:00:00.000Z"
    },
    strategy: {
      strategy_id: "technical_rule_v1",
      total_trades: 18,
      total_return_pct: 12.4,
      total_net_pnl: 2410.15,
      max_drawdown_pct: -4.6,
      sharpe_ratio: 1.18
    },
    ml: null
  };
}

export function mlRunSummaryResponse(): RunSummaryResponse {
  return {
    run_id: "ml-run-001",
    run_name: "ml-aapl-h5",
    workflow_type: "ml_research",
    status: "success",
    started_at: BASE_TIME,
    ended_at: BASE_TIME,
    duration_ms: 4120,
    instrument: {
      symbol: "AAPL",
      asset_class: "stock"
    },
    interval: "1d",
    candle_count: 260,
    candle_source_type: "inline_candles",
    step_results: [
      stepResult("load_candles", 22),
      stepResult("build_features", 180),
      stepResult("train_models", 940),
      stepResult("persist_artifacts", 17)
    ],
    metadata: {
      persisted: true
    },
    candle_time_range: {
      start: "2025-12-01T00:00:00.000Z",
      end: "2026-03-26T00:00:00.000Z"
    },
    strategy: null,
    ml: {
      target_label: "dir_h5",
      task_type: "classification",
      best_model_id: "dummy_cls",
      primary_metric_name: "accuracy",
      best_validation_value: 0.6321,
      best_test_value: 0.6111,
      model_count_executed: 1,
      model_count_skipped: 0,
      warning_count: 0
    }
  };
}

export function historyItem(
  overrides: Partial<RunHistoryItem> & Pick<RunHistoryItem, "run_id">
): RunHistoryItem {
  return {
    run_id: overrides.run_id,
    run_name: overrides.run_name ?? overrides.run_id,
    workflow_type: overrides.workflow_type ?? "strategy_research",
    status: overrides.status ?? "success",
    started_at: overrides.started_at ?? BASE_TIME,
    ended_at: overrides.ended_at ?? BASE_TIME,
    duration_ms: overrides.duration_ms ?? 3210,
    instrument_symbol: overrides.instrument_symbol ?? "AAPL",
    asset_class: overrides.asset_class ?? "stock",
    interval: overrides.interval ?? "1d",
    has_strategy: overrides.has_strategy ?? true,
    has_ml: overrides.has_ml ?? false,
    summary_available: overrides.summary_available ?? true,
    detail_available: overrides.detail_available ?? true,
    updated_at: overrides.updated_at ?? BASE_TIME
  };
}

export function historyListResponse(
  items: RunHistoryItem[],
  warnings: string[] = []
): RunHistoryListResponse {
  return {
    items,
    total: items.length,
    limit: 50,
    offset: 0,
    warnings
  };
}

export function compareRunsResponse(): CompareRunsResponse {
  return {
    mode: "strategy",
    warnings: ["Using normalized summary metrics for compare rows."],
    cards: [
      {
        label: "Total Return %",
        direction: "higher_is_better",
        best_run_id: "strategy-run-001",
        best_value: 12.4,
        worst_run_id: "strategy-run-002",
        worst_value: 8.1
      }
    ],
    rows: [
      {
        run_id: "strategy-run-001",
        run_name: "trend-a",
        workflow_type: "strategy_research",
        status: "success",
        instrument_symbol: "AAPL",
        interval: "1d",
        total_return_pct: 12.4,
        sharpe_ratio: 1.18
      },
      {
        run_id: "strategy-run-002",
        run_name: "trend-b",
        workflow_type: "strategy_research",
        status: "success",
        instrument_symbol: "AAPL",
        interval: "1d",
        total_return_pct: 8.1,
        sharpe_ratio: 0.94
      }
    ]
  };
}

export function savedConfigSummary(
  overrides: Partial<SavedResearchConfigSummary> & Pick<SavedResearchConfigSummary, "id" | "config_type" | "name">
): SavedResearchConfigSummary {
  return {
    id: overrides.id,
    config_type: overrides.config_type,
    name: overrides.name,
    description: overrides.description ?? null,
    config_schema_version: overrides.config_schema_version ?? 1,
    instrument_symbol: overrides.instrument_symbol ?? "AAPL",
    asset_class: overrides.asset_class ?? "stock",
    interval: overrides.interval ?? "1d",
    created_at: overrides.created_at ?? BASE_TIME,
    updated_at: overrides.updated_at ?? BASE_TIME,
    last_used_at: overrides.last_used_at ?? null
  };
}

export function strategySavedConfig(
  overrides: Partial<SavedResearchConfig> = {}
): SavedResearchConfig {
  return {
    ...savedConfigSummary({
      id: "strategy_cfg_001",
      config_type: "strategy",
      name: "trend-template",
      instrument_symbol: "MSFT",
      ...(overrides as Partial<SavedResearchConfigSummary>)
    }),
    payload: {
      instrument: {
        symbol: "MSFT",
        asset_class: "stock"
      },
      interval: "1d",
      candle_source: {
        source_type: "inline_sample",
        inline_bars: 220
      },
      strategy_spec: {
        strategy_id: "technical_rule_v1",
        backtest_config: {
          warmup_bars: 80,
          min_signal_confidence: 0.15
        }
      },
      run_config: {
        run_name: "strategy-msft-template",
        persist_summary: true,
        strict_failures: true
      }
    },
    ...overrides
  };
}

export function mlSavedConfig(
  overrides: Partial<SavedResearchConfig> = {}
): SavedResearchConfig {
  return {
    ...savedConfigSummary({
      id: "ml_cfg_001",
      config_type: "ml",
      name: "ml-template",
      instrument_symbol: "NVDA",
      ...(overrides as Partial<SavedResearchConfigSummary>)
    }),
    payload: {
      instrument: {
        symbol: "NVDA",
        asset_class: "stock"
      },
      interval: "1d",
      candle_source: {
        source_type: "market_data_fetch",
        provider_name: "oanda",
        start: "2026-01-01T00:00:00.000Z",
        end: "2026-03-01T00:00:00.000Z"
      },
      ml_spec: {
        task_type: "classification",
        label_specs: [
          { label_type: "future_return", horizon_bars: 5, name: "ret_h5" },
          { label_type: "direction", horizon_bars: 5, name: "dir_h5" }
        ],
        target_label: "dir_h5",
        model_specs: [{ model_id: "dummy_cls", family: "dummy_classifier" }]
      },
      run_config: {
        run_name: "ml-nvda-template",
        persist_summary: false,
        strict_failures: true
      }
    },
    ...overrides
  };
}

export function savedConfigListResponse(
  items: SavedResearchConfigSummary[]
): SavedResearchConfigListResponse {
  return { items };
}

export function watchlistItem(
  overrides: Partial<WatchlistItem> & Pick<WatchlistItem, "id" | "symbol" | "asset_class">
): WatchlistItem {
  return {
    id: overrides.id,
    symbol: overrides.symbol,
    asset_class: overrides.asset_class,
    source_context: overrides.source_context ?? null,
    created_at: overrides.created_at ?? BASE_TIME,
    updated_at: overrides.updated_at ?? BASE_TIME
  };
}

export function watchlistResponse(items: WatchlistItem[]): WatchlistResponse {
  return { items };
}

export function recentAsset(
  overrides: Partial<RecentAsset> & Pick<RecentAsset, "id" | "symbol" | "asset_class">
): RecentAsset {
  return {
    id: overrides.id,
    symbol: overrides.symbol,
    asset_class: overrides.asset_class,
    source_context: overrides.source_context ?? null,
    last_used_at: overrides.last_used_at ?? BASE_TIME,
    created_at: overrides.created_at ?? BASE_TIME,
    updated_at: overrides.updated_at ?? BASE_TIME
  };
}

export function recentAssetsResponse(items: RecentAsset[]): RecentAssetListResponse {
  return { items };
}

export function recentCompareSet(
  overrides: Partial<RecentCompareSet> & Pick<RecentCompareSet, "id" | "compare_mode" | "run_ids" | "fingerprint">
): RecentCompareSet {
  return {
    id: overrides.id,
    compare_mode: overrides.compare_mode,
    run_ids: overrides.run_ids,
    fingerprint: overrides.fingerprint,
    last_used_at: overrides.last_used_at ?? BASE_TIME,
    created_at: overrides.created_at ?? BASE_TIME,
    updated_at: overrides.updated_at ?? BASE_TIME
  };
}

export function recentCompareSetsResponse(
  items: RecentCompareSet[]
): RecentCompareSetListResponse {
  return { items };
}

export function marketDataPreviewResponse(symbol: string, assetClass: "stock" | "forex") {
  return {
    provider: "oanda",
    instrument: {
      symbol,
      asset_class: assetClass
    },
    interval: assetClass === "stock" ? "1d" : "4h",
    candles: [
      {
        timestamp: "2026-03-20T00:00:00.000Z",
        open: 100,
        high: 102,
        low: 99,
        close: 101
      },
      {
        timestamp: "2026-03-21T00:00:00.000Z",
        open: 101,
        high: 104,
        low: 100,
        close: 103
      },
      {
        timestamp: "2026-03-22T00:00:00.000Z",
        open: 103,
        high: 105,
        low: 102,
        close: 104.5
      }
    ],
    metadata: {
      source: "smoke_fixture"
    }
  };
}

export function assetResearchMemoResponse(
  symbol: string,
  assetClass: "stock" | "forex",
  overrides: Partial<GenerateAssetMemoResponse> = {}
): GenerateAssetMemoResponse {
  const isStock = assetClass === "stock";
  const base: GenerateAssetMemoResponse = {
    asset: {
      symbol,
      asset_class: assetClass,
      name: symbol
    },
    generated_at: BASE_TIME,
    sections: isStock
      ? [
          { title: "Overview", content: "Grounded overview." },
          {
            title: "Recent Price / Performance Context",
            content: "Grounded performance context."
          },
          { title: "Business / Profile Context", content: "Grounded business context." },
          {
            title: "Filing / Fundamental Highlights",
            content: "Live filings are not currently wired, so this section stays within the curated catalog checklist."
          },
          { title: "Risks / Open Questions", content: "Grounded risks." },
          { title: "Bottom-Line Takeaway", content: "Grounded takeaway." }
        ]
      : [
          { title: "Overview", content: "Grounded overview." },
          {
            title: "Recent Price / Performance Context",
            content: "Grounded FX performance context."
          },
          { title: "Macro Context", content: "Grounded macro context." },
          { title: "Key Drivers", content: "Grounded drivers." },
          { title: "Risks / Open Questions", content: "Grounded risks." },
          { title: "Bottom-Line Takeaway", content: "Grounded takeaway." }
        ],
    grounding: [
      {
        source: "catalog",
        status: "used",
        detail: "Using the shared curated asset catalog."
      }
    ],
    warnings: isStock
      ? ["Live filings and fundamentals data are not currently wired."]
      : []
  };
  return {
    ...base,
    ...overrides,
    asset: { ...base.asset, ...(overrides.asset ?? {}) },
    sections: overrides.sections ?? base.sections,
    grounding: overrides.grounding ?? base.grounding,
    warnings: overrides.warnings ?? base.warnings
  };
}

export function assetResearchQuestionResponse(
  symbol: string,
  assetClass: "stock" | "forex",
  question: string,
  overrides: Partial<AskAssetResearchQuestionResponse> = {}
): AskAssetResearchQuestionResponse {
  const base: AskAssetResearchQuestionResponse = {
    asset: {
      symbol,
      asset_class: assetClass,
      name: symbol
    },
    question,
    generated_at: BASE_TIME,
    answer: "Grounded answer.",
    grounding: [
      {
        source: "recent_run_history",
        status: "used",
        detail: "Loaded recent runs for this asset."
      }
    ],
    warnings: []
  };
  return {
    ...base,
    ...overrides,
    asset: { ...base.asset, ...(overrides.asset ?? {}) },
    grounding: overrides.grounding ?? base.grounding,
    warnings: overrides.warnings ?? base.warnings
  };
}

export function paperStateResponse(
  overrides: Partial<PaperStateResponse> = {}
): PaperStateResponse {
  const base: PaperStateResponse = {
    config: {
      account_id: "paper-main",
      base_currency: "USD",
      initial_cash: 100000,
      allow_short: false,
      default_spread_bps: 1,
      default_slippage_bps: 2,
      commission_bps: 0,
      commission_fixed: 0
    },
    account: {
      account_id: "paper-main",
      base_currency: "USD",
      cash: 98250,
      realized_pnl: 125.25,
      unrealized_pnl: 45,
      equity: 98420.25,
      total_fees: 6,
      updated_at: BASE_TIME
    },
    positions: [
      {
        instrument: {
          symbol: "AAPL",
          asset_class: "stock"
        },
        quantity: 10,
        average_price: 175.5,
        mark_price: 180,
        unrealized_pnl: 45,
        realized_pnl: 0,
        updated_at: BASE_TIME
      }
    ],
    open_orders: [
      {
        order_id: "ord-100",
        instrument: {
          symbol: "MSFT",
          asset_class: "stock"
        },
        side: "buy",
        order_type: "limit",
        quantity: 5,
        status: "open",
        created_at: BASE_TIME,
        updated_at: BASE_TIME,
        limit_price: 410,
        reference_price: 409.5,
        client_order_id: "cli-100",
        rejection_reason: null,
        filled_quantity: 0,
        average_fill_price: null,
        metadata: {}
      }
    ],
    fills: [
      {
        fill_id: "fill-100",
        order_id: "ord-099",
        instrument: {
          symbol: "AAPL",
          asset_class: "stock"
        },
        side: "buy",
        quantity: 10,
        fill_price: 175.5,
        notional: 1755,
        commission: 1,
        spread_cost: 0.25,
        slippage_cost: 0.1,
        realized_pnl_delta: 0,
        timestamp: BASE_TIME
      }
    ],
    price_book: {
      AAPL: 180,
      MSFT: 409.5
    },
    updated_at: BASE_TIME
  };

  return {
    ...base,
    ...overrides,
    config: { ...base.config, ...(overrides.config ?? {}) },
    account: { ...base.account, ...(overrides.account ?? {}) },
    positions: overrides.positions ?? base.positions,
    open_orders: overrides.open_orders ?? base.open_orders,
    fills: overrides.fills ?? base.fills,
    price_book: overrides.price_book ?? base.price_book
  };
}

export function settingsResponse(): SystemSettingsResponse {
  return {
    runtime: {
      app_name: "capstone-api",
      api_prefix: "/api/v1",
      host: "127.0.0.1",
      port: 8000,
      cors_allowed_origins: ["http://127.0.0.1:5173"],
      generated_at: BASE_TIME
    },
    feature_flags: {
      research_api_enabled: true,
      history_api_enabled: true,
      compare_api_enabled: true,
      paper_trading_enabled: true,
      live_execution_status_enabled: true,
      live_execution_submit_enabled: false
    },
    storage: {
      run_output_dir: "artifacts/runs",
      paper_trading_dir: "artifacts/paper"
    },
    paper_defaults: {
      account_id: "paper-main",
      base_currency: "USD",
      initial_cash: 100000,
      allow_short: false,
      spread_bps: 1,
      slippage_bps: 2,
      commission_bps: 0,
      commission_fixed: 0
    },
    live_safety: {
      enabled: false,
      allow_order_submission: false,
      submit_feature_enabled: false,
      effective_submission_enabled: false,
      broker_name: "oanda_stub",
      request_timeout_seconds: 10,
      confirmation_phrase: "EXECUTE LIVE ORDER",
      attempt_log_path: "artifacts/live/attempts.jsonl",
      credentials_configured: false,
      environment: "practice"
    },
    providers: {
      oanda_market_data_enabled: true,
      oanda_market_data_configured: true,
      live_oanda_configured: false
    }
  };
}

export function liveReadinessResponse(
  overrides: Partial<LiveExecutionReadinessResponse> = {}
): LiveExecutionReadinessResponse {
  const defaultChecks = [
    {
      name: "feature_enabled",
      passed: false,
      code: "feature_disabled",
      message: "Live submission feature flag is disabled."
    },
    {
      name: "credentials_configured",
      passed: false,
      code: "credentials_missing",
      message: "Broker credentials are not configured."
    }
  ];

  return {
    generated_at: BASE_TIME,
    broker_name: "oanda_stub",
    enabled: false,
    submission_allowed: false,
    configured: false,
    state: "disabled",
    message: "Live execution is disabled until every guard is satisfied.",
    manual_submission_ready: false,
    confirmation_phrase: "EXECUTE LIVE ORDER",
    ...overrides,
    checks: overrides.checks ?? defaultChecks
  };
}

export function liveAttemptsResponse(): LiveExecutionAttemptsResponse {
  return {
    attempts: [
      {
        attempt_id: "attempt-001",
        timestamp: BASE_TIME,
        broker_name: "oanda_stub",
        idempotency_key: "idem-001",
        request_summary: {
          symbol: "EUR_USD",
          side: "buy"
        },
        guard_checks: [
          {
            name: "feature_enabled",
            passed: false,
            code: "feature_disabled",
            message: "Live submission feature flag is disabled."
          }
        ],
        accepted: false,
        status: "rejected",
        rejection_code: "feature_disabled",
        rejection_message: "Live submission feature flag is disabled.",
        external_order_id: null
      }
    ]
  };
}

export function liveValidationResponse(): LiveIntentValidationResponse {
  return {
    accepted: false,
    reasons: ["Live execution remains fail-closed until submission is explicitly enabled."],
    normalized_intent: null,
    broker_payload_preview: {
      symbol: "EUR_USD",
      units: 1000,
      side: "buy"
    }
  };
}

export function manualLiveRejectedResponse(): ManualLiveSubmitResponse {
  return {
    accepted: false,
    status: "rejected",
    attempt_id: "attempt-002",
    broker_name: "oanda_stub",
    rejection_code: "manual_confirmation_required",
    rejection_message: "Manual confirmation phrase did not satisfy guarded live submission requirements.",
    external_order_id: null,
    broker_payload: null,
    guard_checks: [
      {
        name: "confirmation_phrase",
        passed: false,
        code: "manual_confirmation_required",
        message: "Manual confirmation phrase did not satisfy guarded live submission requirements."
      }
    ]
  };
}
