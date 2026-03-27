export type AssetClass = "stock" | "forex";
export type BarInterval = "1m" | "5m" | "15m" | "30m" | "1h" | "4h" | "1d";

export interface ApiErrorEnvelope {
  error: {
    code: string;
    message: string;
    details?: Record<string, unknown> | null;
    request_id?: string | null;
  };
}

export interface Instrument {
  symbol: string;
  asset_class: AssetClass;
  venue?: string | null;
  quote_currency?: string | null;
}

export interface Candle {
  timestamp: string;
  open: number;
  high: number;
  low: number;
  close: number;
  volume?: number | null;
}

export interface InlineCandleSource {
  source_type: "inline_candles";
  candles: Candle[];
}

export interface MarketDataFetchSource {
  source_type: "market_data_fetch";
  provider_name: string;
  start: string;
  end: string;
  limit?: number;
}

export type CandleSource = InlineCandleSource | MarketDataFetchSource;

export interface RunConfig {
  run_id?: string;
  run_name?: string;
  random_seed?: number;
  strict_failures?: boolean;
  persist_summary?: boolean;
  output_dir?: string;
  metadata?: Record<string, unknown>;
}

export interface StrategyRunRequest {
  instrument: Instrument;
  interval: BarInterval;
  candle_source: CandleSource;
  strategy_spec?: {
    strategy_id?: string;
    backtest_config?: {
      warmup_bars?: number;
      min_signal_confidence?: number;
      initial_capital?: number;
      allow_short?: boolean;
      allow_flip?: boolean;
      position_notional_fraction?: number;
    };
  };
  run_config?: RunConfig;
}

export type LabelSpec =
  | {
      label_type: "future_return";
      horizon_bars: number;
      name?: string;
      price_field?: "close";
    }
  | {
      label_type: "direction";
      horizon_bars: number;
      threshold?: number;
      name?: string;
      price_field?: "close";
    };

export interface MLRunRequest {
  instrument: Instrument;
  interval: BarInterval;
  candle_source: CandleSource;
  ml_spec?: {
    feature_spec?: {
      return_windows?: number[];
      log_return_windows?: number[];
      volatility_windows?: number[];
      momentum_windows?: number[];
      sma_windows?: number[];
      sma_crossover_pairs?: [number, number][];
      atr_windows?: number[];
      zscore_windows?: number[];
      include_candle_structure?: boolean;
      include_volume_features?: boolean;
      volume_zscore_windows?: number[];
    };
    label_specs?: LabelSpec[];
    split_spec?: {
      train_fraction?: number;
      validation_fraction?: number;
      test_fraction?: number;
      gap_bars?: number;
    };
    missing_volume_policy?: "skip_volume_features" | "require_volume";
    missing_value_policy?: "drop_row";
    task_type?: "regression" | "classification";
    target_label?: string;
    model_specs?: Array<{
      model_id: string;
      family:
        | "dummy_regressor"
        | "dummy_classifier"
        | "ridge_regressor_np"
        | "linear_regression_sklearn"
        | "logistic_regression_sklearn"
        | "random_forest_regressor_sklearn"
        | "random_forest_classifier_sklearn"
        | "gradient_boosting_regressor_sklearn"
        | "gradient_boosting_classifier_sklearn";
      hyperparameters?: Record<string, unknown>;
      requires_optional_dependency?: boolean;
    }>;
  };
  run_config?: RunConfig;
}

export interface HybridRunRequest {
  instrument: Instrument;
  interval: BarInterval;
  candle_source: CandleSource;
  strategy_spec?: StrategyRunRequest["strategy_spec"];
  ml_spec?: MLRunRequest["ml_spec"];
  run_config?: RunConfig;
}

export interface StepResult {
  step_name: string;
  status: "success" | "failed" | "skipped" | string;
  started_at: string;
  ended_at: string;
  duration_ms: number;
  error_type?: string | null;
  error_message?: string | null;
  metadata?: Record<string, unknown>;
}

export interface RunSummaryResponse {
  run_id: string;
  run_name: string;
  workflow_type: string;
  status: string;
  started_at: string;
  ended_at: string;
  duration_ms: number;
  instrument: Instrument;
  interval: BarInterval;
  candle_count: number;
  candle_source_type: string;
  step_results: StepResult[];
  metadata: Record<string, unknown>;
  candle_time_range?: { start: string; end: string } | null;
  strategy?: {
    strategy_id: string;
    total_trades: number;
    total_return_pct: number;
    total_net_pnl: number;
    max_drawdown_pct: number;
    sharpe_ratio?: number | null;
  } | null;
  ml?: {
    target_label: string;
    task_type: "regression" | "classification";
    best_model_id?: string | null;
    primary_metric_name?: string | null;
    best_validation_value?: number | null;
    best_test_value?: number | null;
    model_count_executed: number;
    model_count_skipped: number;
    warning_count: number;
  } | null;
}

export interface CapabilitiesResponse {
  workflows: string[];
  strategies: string[];
  providers: string[];
  intervals: string[];
  asset_classes: string[];
  model_families: string[];
  feature_flags?: {
    research_api_enabled: boolean;
    history_api_enabled: boolean;
    compare_api_enabled: boolean;
    paper_trading_enabled: boolean;
    live_execution_status_enabled: boolean;
    live_execution_submit_enabled: boolean;
  } | null;
  paper_trading?: {
    supported_order_types: string[];
    supported_order_sides: string[];
    supports_short: boolean;
    supports_signal_intents: boolean;
    supported_asset_classes: AssetClass[];
  } | null;
  live_execution?: {
    broker_name: string;
    enabled: boolean;
    submission_allowed: boolean;
    configured: boolean;
    state: string;
    message: string;
    supported_order_types: string[];
    supported_order_sides: string[];
    supported_asset_classes: AssetClass[];
    supports_short: boolean;
    supports_cancel: boolean;
    supports_submit: boolean;
  } | null;
}

export interface HealthResponse {
  status: string;
  service: string;
  version: string;
  timestamp: string;
}

export interface MarketDataPreviewRequest {
  provider_name: string;
  instrument: Instrument;
  interval: BarInterval;
  start: string;
  end: string;
  limit?: number;
}

export interface MarketDataPreviewResponse {
  provider: string;
  instrument: Instrument;
  interval: BarInterval;
  candles: Candle[];
  metadata: Record<string, unknown>;
}

export interface StoredRunSummaryListItem {
  run_id: string;
  run_name?: string | null;
  workflow_type?: string | null;
  status?: string | null;
  started_at?: string | null;
  ended_at?: string | null;
  summary_path: string;
}

export interface StoredRunSummaryListResponse {
  runs: StoredRunSummaryListItem[];
}

export interface StrategyTradeRow {
  entry_time: string;
  exit_time: string;
  direction: string;
  entry_price: number;
  exit_price: number;
  units: number;
  gross_pnl: number;
  net_pnl: number;
  return_pct: number;
  bars_held: number;
  exit_reason: string;
}

export interface EquityPointDetail {
  timestamp: string;
  equity: number;
  cash: number;
  unrealized_pnl: number;
  drawdown_pct: number;
}

export interface DrawdownPointDetail {
  timestamp: string;
  drawdown_pct: number;
}

export interface DrawdownEpisodeDetail {
  peak_time: string;
  trough_time: string;
  recovery_time?: string | null;
  depth_pct: number;
  duration_bars: number;
  recovery_bars?: number | null;
}

export interface StrategyDetailResponse {
  backtest_summary: Record<string, unknown>;
  performance: Record<string, unknown>;
  trade_analysis: Record<string, unknown>;
  risk: Record<string, unknown>;
  assumptions: Record<string, string>;
  equity_curve: EquityPointDetail[];
  drawdown_curve: DrawdownPointDetail[];
  trades: StrategyTradeRow[];
  drawdown_episodes: DrawdownEpisodeDetail[];
}

export interface ModelComparisonEntryDetail {
  model_id: string;
  family: string;
  primary_metric_name: string;
  validation_value?: number | null;
  test_value?: number | null;
  higher_is_better: boolean;
}

export interface FeatureImportanceItem {
  feature: string;
  score: number;
}

export interface ModelReportDetail {
  model_id: string;
  family: string;
  task_type: string;
  skipped: boolean;
  skip_reason?: string | null;
  metrics_by_split: Record<string, Record<string, unknown>>;
  feature_importance?: FeatureImportanceItem[] | null;
  warnings: string[];
}

export interface MLDetailResponse {
  target_label: string;
  task_type: "regression" | "classification";
  dataset_metadata: Record<string, unknown>;
  comparison_table: ModelComparisonEntryDetail[];
  model_reports: ModelReportDetail[];
  run_metadata: Record<string, unknown>;
  warnings: string[];
}

export interface RunDetailResponse {
  summary: RunSummaryResponse;
  strategy_detail?: StrategyDetailResponse | null;
  ml_detail?: MLDetailResponse | null;
}
