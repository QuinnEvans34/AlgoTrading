import type {
  ModelReportDetail,
  RunDetailResponse
} from "../api/types";
import { asNumber, formatNumber, formatPercent } from "./formatters";
import type { MLResultView, MetricItem, StrategyResultView } from "./types";

function toMetric(label: string, value: string): MetricItem {
  return { label, value };
}

function topFeatureImportance(
  modelReports: ModelReportDetail[]
): Array<{ feature: string; score: number }> {
  const best = modelReports.find(
    (report) => !report.skipped && report.feature_importance && report.feature_importance.length > 0
  );
  return best?.feature_importance?.slice(0, 15) ?? [];
}

export function toStrategyResultView(
  detail: RunDetailResponse
): StrategyResultView | null {
  if (!detail.strategy_detail) {
    return null;
  }
  const strategySummary = detail.summary.strategy;
  const backtestSummary = detail.strategy_detail.backtest_summary;
  const tradeAnalysis = detail.strategy_detail.trade_analysis;
  const risk = detail.strategy_detail.risk;
  const metrics: MetricItem[] = [
    toMetric(
      "Total Return",
      formatPercent(asNumber(backtestSummary["total_return_pct"]))
    ),
    toMetric(
      "Net PnL",
      formatNumber(asNumber(backtestSummary["total_net_pnl"]))
    ),
    toMetric(
      "Max Drawdown",
      formatPercent(asNumber(backtestSummary["max_drawdown_pct"]))
    ),
    toMetric(
      "Sharpe",
      formatNumber(asNumber(backtestSummary["sharpe_ratio"]), 3)
    ),
    toMetric(
      "Trades",
      String(
        asNumber(backtestSummary["total_trades"]) ??
          strategySummary?.total_trades ??
          0
      )
    ),
    toMetric(
      "Win Rate",
      formatPercent(asNumber(tradeAnalysis["win_rate_pct"]))
    ),
    toMetric(
      "Profit Factor",
      formatNumber(asNumber(tradeAnalysis["profit_factor"]), 3)
    ),
    toMetric(
      "Volatility",
      formatPercent(asNumber(risk["volatility_pct"]))
    )
  ];

  return {
    run: detail.summary,
    metrics,
    equityPoints: detail.strategy_detail.equity_curve.map((point) => ({
      timestamp: point.timestamp,
      value: point.equity
    })),
    drawdownPoints: detail.strategy_detail.drawdown_curve.map((point) => ({
      timestamp: point.timestamp,
      value: point.drawdown_pct
    })),
    trades: detail.strategy_detail.trades,
    tradeSummary: tradeAnalysis,
    riskSummary: risk
  };
}

export function toMLResultView(detail: RunDetailResponse): MLResultView | null {
  if (!detail.ml_detail) {
    return null;
  }
  const summary = detail.summary.ml;
  const metrics: MetricItem[] = [
    toMetric("Task", summary?.task_type ?? detail.ml_detail.task_type),
    toMetric("Target Label", detail.ml_detail.target_label),
    toMetric("Best Model", summary?.best_model_id ?? "n/a"),
    toMetric("Primary Metric", summary?.primary_metric_name ?? "n/a"),
    toMetric(
      "Best Validation",
      formatNumber(summary?.best_validation_value ?? null, 4)
    ),
    toMetric("Best Test", formatNumber(summary?.best_test_value ?? null, 4)),
    toMetric("Models Executed", String(summary?.model_count_executed ?? 0)),
    toMetric("Warnings", String(detail.ml_detail.warnings.length))
  ];

  return {
    run: detail.summary,
    metrics,
    comparisonRows: detail.ml_detail.comparison_table,
    modelReports: detail.ml_detail.model_reports,
    featureImportance: topFeatureImportance(detail.ml_detail.model_reports),
    warnings: detail.ml_detail.warnings,
    datasetMetadata: detail.ml_detail.dataset_metadata
  };
}
