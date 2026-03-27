import { useEffect, useState } from "react";
import { Link, useParams } from "react-router-dom";

import { ErrorAlert } from "../components/common/ErrorAlert";
import { LoadingState } from "../components/common/LoadingState";
import { DrawdownChart } from "../components/results/DrawdownChart";
import { EquityCurveChart } from "../components/results/EquityCurveChart";
import { MetricsGrid } from "../components/results/MetricsGrid";
import { ResultDebugPanel } from "../components/results/ResultDebugPanel";
import { RunSummaryPanel } from "../components/results/RunSummaryPanel";
import { StepResultsTable } from "../components/results/StepResultsTable";
import { TradeTable } from "../components/results/TradeTable";
import { fetchStoredRunDetail } from "../lib/api/results";
import type { RunDetailResponse } from "../lib/api/types";
import { toStrategyResultView } from "../lib/results/adapters";

function SummaryMapPanel({
  title,
  values
}: {
  title: string;
  values: Record<string, unknown>;
}) {
  const entries = Object.entries(values).filter(([, value]) =>
    ["number", "string", "boolean"].includes(typeof value)
  );
  if (entries.length === 0) {
    return null;
  }
  return (
    <section className="result-panel">
      <h2>{title}</h2>
      <table className="data-table compact">
        <thead>
          <tr>
            <th>Metric</th>
            <th>Value</th>
          </tr>
        </thead>
        <tbody>
          {entries.map(([key, value]) => (
            <tr key={key}>
              <td>{key}</td>
              <td>{String(value)}</td>
            </tr>
          ))}
        </tbody>
      </table>
    </section>
  );
}

export function StrategyResultPage() {
  const { runId } = useParams<{ runId: string }>();
  const [detail, setDetail] = useState<RunDetailResponse | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<unknown>(null);

  useEffect(() => {
    const resolvedRunId = runId;
    if (!resolvedRunId) {
      return;
    }
    async function load() {
      setLoading(true);
      setError(null);
      try {
        const response = await fetchStoredRunDetail(resolvedRunId!);
        setDetail(response);
      } catch (err) {
        setError(err);
        setDetail(null);
      } finally {
        setLoading(false);
      }
    }
    void load();
  }, [runId]);

  const view = detail ? toStrategyResultView(detail) : null;

  return (
    <section className="page">
      <h2>Strategy Run Detail</h2>
      <p>
        Run ID: <code>{runId ?? "n/a"}</code>{" "}
        <Link to="/runs">Back to stored runs</Link>
      </p>

      {loading ? <LoadingState label="Loading strategy result detail..." /> : null}
      {error ? <ErrorAlert error={error} /> : null}

      {detail ? <RunSummaryPanel result={detail.summary} /> : null}
      {detail ? <StepResultsTable steps={detail.summary.step_results} /> : null}

      {detail && !view ? (
        <section className="result-panel">
          <p>
            This run has no strategy detail payload. It may be an older persisted
            run with summary-only output.
          </p>
        </section>
      ) : null}

      {view ? (
        <>
          <MetricsGrid title="Strategy KPIs" metrics={view.metrics} />
          <EquityCurveChart points={view.equityPoints} />
          <DrawdownChart points={view.drawdownPoints} />
          <TradeTable trades={view.trades} />
          <SummaryMapPanel title="Trade Analytics Snapshot" values={view.tradeSummary} />
          <SummaryMapPanel title="Risk Snapshot" values={view.riskSummary} />
          <ResultDebugPanel payload={detail} />
        </>
      ) : null}
    </section>
  );
}
