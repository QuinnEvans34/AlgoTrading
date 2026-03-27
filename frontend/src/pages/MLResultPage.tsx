import { useEffect, useState } from "react";
import { Link, useParams } from "react-router-dom";

import { ErrorAlert } from "../components/common/ErrorAlert";
import { LoadingState } from "../components/common/LoadingState";
import { FeatureImportancePanel } from "../components/results/FeatureImportancePanel";
import { MetricsGrid } from "../components/results/MetricsGrid";
import { ModelMetricsPanel } from "../components/results/ModelMetricsPanel";
import { ResultDebugPanel } from "../components/results/ResultDebugPanel";
import { RunSummaryPanel } from "../components/results/RunSummaryPanel";
import { StepResultsTable } from "../components/results/StepResultsTable";
import { fetchStoredRunDetail } from "../lib/api/results";
import type { RunDetailResponse } from "../lib/api/types";
import { toMLResultView } from "../lib/results/adapters";

function MetadataPanel({ metadata }: { metadata: Record<string, unknown> }) {
  const entries = Object.entries(metadata).filter(([, value]) =>
    ["number", "string", "boolean"].includes(typeof value)
  );
  if (entries.length === 0) {
    return null;
  }
  return (
    <section className="result-panel">
      <h2>Dataset Metadata Snapshot</h2>
      <table className="data-table compact">
        <thead>
          <tr>
            <th>Field</th>
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

export function MLResultPage() {
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

  const view = detail ? toMLResultView(detail) : null;

  return (
    <section className="page">
      <h2>ML Run Detail</h2>
      <p>
        Run ID: <code>{runId ?? "n/a"}</code> <Link to="/runs">Back to stored runs</Link>
      </p>

      {loading ? <LoadingState label="Loading ML result detail..." /> : null}
      {error ? <ErrorAlert error={error} /> : null}

      {detail ? <RunSummaryPanel result={detail.summary} /> : null}
      {detail ? <StepResultsTable steps={detail.summary.step_results} /> : null}

      {detail && !view ? (
        <section className="result-panel">
          <p>
            This run has no ML detail payload. It may be an older persisted run
            with summary-only output.
          </p>
        </section>
      ) : null}

      {view ? (
        <>
          <MetricsGrid title="ML KPIs" metrics={view.metrics} />
          <ModelMetricsPanel
            comparisonRows={view.comparisonRows}
            modelReports={view.modelReports}
          />
          <FeatureImportancePanel items={view.featureImportance} />
          <MetadataPanel metadata={view.datasetMetadata} />
          {view.warnings.length > 0 ? (
            <section className="result-panel">
              <h2>Warnings</h2>
              <ul className="simple-list">
                {view.warnings.map((warning) => (
                  <li key={warning}>{warning}</li>
                ))}
              </ul>
            </section>
          ) : null}
          <ResultDebugPanel payload={detail} />
        </>
      ) : null}
    </section>
  );
}
