import type { RunSummaryResponse } from "../../lib/api/types";

interface RunSummaryPanelProps {
  result: RunSummaryResponse;
}

export function RunSummaryPanel({ result }: RunSummaryPanelProps) {
  return (
    <section className="result-panel">
      <h2>Run Summary</h2>
      <div className="summary-grid">
        <Info label="Run ID" value={result.run_id} />
        <Info label="Run Name" value={result.run_name} />
        <Info label="Workflow" value={result.workflow_type} />
        <Info label="Status" value={result.status} />
        <Info label="Instrument" value={result.instrument.symbol} />
        <Info label="Asset Class" value={result.instrument.asset_class} />
        <Info label="Interval" value={result.interval} />
        <Info label="Candles" value={String(result.candle_count)} />
      </div>

      {result.strategy ? (
        <section className="nested-panel">
          <h3>Strategy Summary</h3>
          <div className="summary-grid">
            <Info label="Strategy" value={result.strategy.strategy_id} />
            <Info label="Trades" value={String(result.strategy.total_trades)} />
            <Info
              label="Total Return %"
              value={result.strategy.total_return_pct.toFixed(2)}
            />
            <Info
              label="Total Net PnL"
              value={result.strategy.total_net_pnl.toFixed(2)}
            />
            <Info
              label="Max Drawdown %"
              value={result.strategy.max_drawdown_pct.toFixed(2)}
            />
            <Info
              label="Sharpe"
              value={
                result.strategy.sharpe_ratio === null ||
                result.strategy.sharpe_ratio === undefined
                  ? "n/a"
                  : result.strategy.sharpe_ratio.toFixed(3)
              }
            />
          </div>
        </section>
      ) : null}

      {result.ml ? (
        <section className="nested-panel">
          <h3>ML Summary</h3>
          <div className="summary-grid">
            <Info label="Task" value={result.ml.task_type} />
            <Info label="Target Label" value={result.ml.target_label} />
            <Info label="Best Model" value={result.ml.best_model_id ?? "n/a"} />
            <Info
              label="Primary Metric"
              value={result.ml.primary_metric_name ?? "n/a"}
            />
            <Info
              label="Best Validation"
              value={
                result.ml.best_validation_value === null ||
                result.ml.best_validation_value === undefined
                  ? "n/a"
                  : result.ml.best_validation_value.toFixed(4)
              }
            />
            <Info
              label="Best Test"
              value={
                result.ml.best_test_value === null ||
                result.ml.best_test_value === undefined
                  ? "n/a"
                  : result.ml.best_test_value.toFixed(4)
              }
            />
          </div>
        </section>
      ) : null}
    </section>
  );
}

interface InfoProps {
  label: string;
  value: string;
}

function Info({ label, value }: InfoProps) {
  return (
    <div className="info-item">
      <span>{label}</span>
      <strong>{value}</strong>
    </div>
  );
}

