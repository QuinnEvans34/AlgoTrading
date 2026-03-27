import type { RunDetailResponse, RunSummaryResponse } from "../api/types";

export interface RunHistoryItem {
  run_id: string;
  run_name: string;
  workflow_type: string;
  status: string;
  started_at?: string | null;
  ended_at?: string | null;
  duration_ms?: number | null;
  instrument_symbol: string;
  asset_class?: string | null;
  interval?: string | null;
  has_strategy: boolean;
  has_ml: boolean;
  summary_available: boolean;
  detail_available: boolean;
  updated_at: string;
}

export interface RunHistoryListResponse {
  items: RunHistoryItem[];
  total: number;
  limit: number;
  offset: number;
  warnings: string[];
}

export interface RunManifest {
  schema_version: number;
  run_id: string;
  run_name: string;
  workflow_type: string;
  status: string;
  started_at?: string | null;
  ended_at?: string | null;
  duration_ms?: number | null;
  instrument_symbol: string;
  asset_class?: string | null;
  interval?: string | null;
  candle_count?: number | null;
  has_strategy: boolean;
  has_ml: boolean;
  summary_path: string;
  detail_path?: string | null;
  created_at?: string | null;
  updated_at?: string | null;
  synthetic: boolean;
}

export interface HistoryReadResponse {
  manifest: RunManifest;
  summary: RunSummaryResponse;
  detail: RunDetailResponse;
}

export type CompareMode = "auto" | "strategy" | "ml";

export interface CompareRunsRequest {
  run_ids: string[];
  mode?: CompareMode;
}

export interface CompareMetricCard {
  label: string;
  direction: string;
  best_run_id?: string | null;
  best_value?: number | null;
  worst_run_id?: string | null;
  worst_value?: number | null;
}

export interface CompareRunsResponse {
  mode: "strategy" | "ml";
  warnings: string[];
  cards: CompareMetricCard[];
  rows: Array<Record<string, unknown>>;
}
