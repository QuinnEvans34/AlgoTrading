import type {
  ModelComparisonEntryDetail,
  ModelReportDetail,
  RunDetailResponse,
  StrategyTradeRow
} from "../api/types";

export interface MetricItem {
  label: string;
  value: string;
}

export interface ChartPoint {
  timestamp: string;
  value: number;
}

export interface StrategyResultView {
  run: RunDetailResponse["summary"];
  metrics: MetricItem[];
  equityPoints: ChartPoint[];
  drawdownPoints: ChartPoint[];
  trades: StrategyTradeRow[];
  tradeSummary: Record<string, unknown>;
  riskSummary: Record<string, unknown>;
}

export interface MLResultView {
  run: RunDetailResponse["summary"];
  metrics: MetricItem[];
  comparisonRows: ModelComparisonEntryDetail[];
  modelReports: ModelReportDetail[];
  featureImportance: Array<{ feature: string; score: number }>;
  warnings: string[];
  datasetMetadata: Record<string, unknown>;
}
