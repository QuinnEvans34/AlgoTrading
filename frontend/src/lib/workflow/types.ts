import type {
  AssetClass,
  BarInterval,
  Instrument,
  MLRunRequest,
  StrategyRunRequest
} from "../api/types";
import type { CompareMode } from "../history/types";

export type SavedConfigType = "strategy" | "ml";

export interface InlineSampleCandleSource {
  source_type: "inline_sample";
  inline_bars: number;
}

export interface SavedConfigMarketDataFetchSource {
  source_type: "market_data_fetch";
  provider_name: string;
  start: string;
  end: string;
  limit?: number;
}

export type SavedConfigCandleSource =
  | InlineSampleCandleSource
  | SavedConfigMarketDataFetchSource;

export interface SavedConfigRunDefaults {
  run_name?: string;
  random_seed?: number;
  strict_failures?: boolean;
  persist_summary?: boolean;
  metadata?: Record<string, unknown>;
}

export interface SavedStrategyConfigPayload {
  instrument: Instrument;
  interval: BarInterval;
  candle_source: SavedConfigCandleSource;
  strategy_spec?: StrategyRunRequest["strategy_spec"];
  run_config?: SavedConfigRunDefaults;
}

export interface SavedMLConfigPayload {
  instrument: Instrument;
  interval: BarInterval;
  candle_source: SavedConfigCandleSource;
  ml_spec?: MLRunRequest["ml_spec"];
  run_config?: SavedConfigRunDefaults;
}

export type SavedConfigPayload = SavedStrategyConfigPayload | SavedMLConfigPayload;

export interface SavedResearchConfigSummary {
  id: string;
  config_type: SavedConfigType;
  name: string;
  description?: string | null;
  config_schema_version: number;
  instrument_symbol: string;
  asset_class: AssetClass | string;
  interval: BarInterval | string;
  created_at: string;
  updated_at: string;
  last_used_at?: string | null;
}

export interface SavedResearchConfig extends SavedResearchConfigSummary {
  payload: SavedConfigPayload;
}

export interface SavedResearchConfigListResponse {
  items: SavedResearchConfigSummary[];
}

export interface SavedResearchConfigCreateRequest {
  config_type: SavedConfigType;
  name: string;
  description?: string | null;
  config_schema_version?: number;
  payload: SavedConfigPayload;
}

export type SavedResearchConfigUpdateRequest = SavedResearchConfigCreateRequest;

export interface DeleteWorkflowObjectResponse {
  deleted: boolean;
}

export interface WatchlistItem {
  id: string;
  symbol: string;
  asset_class: AssetClass | string;
  source_context?: string | null;
  created_at: string;
  updated_at: string;
}

export interface WatchlistResponse {
  items: WatchlistItem[];
}

export interface WatchlistItemWriteRequest {
  symbol: string;
  asset_class: AssetClass | string;
  source_context?: string | null;
}

export interface RecentAsset {
  id: string;
  symbol: string;
  asset_class: AssetClass | string;
  source_context?: string | null;
  last_used_at: string;
  created_at: string;
  updated_at: string;
}

export interface RecentAssetListResponse {
  items: RecentAsset[];
}

export interface RecentAssetTouchRequest {
  symbol: string;
  asset_class: AssetClass | string;
  source_context?: string | null;
}

export interface RecentCompareSet {
  id: string;
  compare_mode: CompareMode;
  run_ids: string[];
  fingerprint: string;
  last_used_at: string;
  created_at: string;
  updated_at: string;
}

export interface RecentCompareSetListResponse {
  items: RecentCompareSet[];
}

export interface RecentCompareTouchRequest {
  compare_mode: CompareMode;
  run_ids: string[];
}
