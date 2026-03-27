export interface RuntimeStatus {
  app_name: string;
  api_prefix: string;
  host: string;
  port: number;
  cors_allowed_origins: string[];
  generated_at: string;
}

export interface FeatureFlagsStatus {
  research_api_enabled: boolean;
  history_api_enabled: boolean;
  compare_api_enabled: boolean;
  paper_trading_enabled: boolean;
  live_execution_status_enabled: boolean;
  live_execution_submit_enabled: boolean;
}

export interface StorageStatus {
  run_output_dir: string;
  paper_trading_dir: string;
}

export interface PaperDefaultsStatus {
  account_id: string;
  base_currency: string;
  initial_cash: number;
  allow_short: boolean;
  spread_bps: number;
  slippage_bps: number;
  commission_bps: number;
  commission_fixed: number;
}

export interface LiveSafetyStatus {
  enabled: boolean;
  allow_order_submission: boolean;
  submit_feature_enabled: boolean;
  effective_submission_enabled: boolean;
  broker_name: string;
  request_timeout_seconds: number;
  confirmation_phrase: string;
  attempt_log_path: string;
  credentials_configured: boolean;
  environment: string;
}

export interface ProviderStatus {
  oanda_market_data_enabled: boolean;
  oanda_market_data_configured: boolean;
  live_oanda_configured: boolean;
}

export interface SystemSettingsResponse {
  runtime: RuntimeStatus;
  feature_flags: FeatureFlagsStatus;
  storage: StorageStatus;
  paper_defaults: PaperDefaultsStatus;
  live_safety: LiveSafetyStatus;
  providers: ProviderStatus;
}
