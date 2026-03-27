import type {
  ModelComparisonEntryDetail,
  ModelReportDetail
} from "../../lib/api/types";

interface ModelMetricsPanelProps {
  comparisonRows: ModelComparisonEntryDetail[];
  modelReports: ModelReportDetail[];
}

function metricKeys(report: ModelReportDetail): string[] {
  const keySet = new Set<string>();
  Object.values(report.metrics_by_split).forEach((splitMetrics) => {
    Object.keys(splitMetrics).forEach((key) => keySet.add(key));
  });
  return Array.from(keySet).sort();
}

function formatMetric(value: unknown): string {
  if (typeof value === "number") {
    return Number.isInteger(value) ? String(value) : value.toFixed(4);
  }
  if (value === null || value === undefined) {
    return "n/a";
  }
  return String(value);
}

export function ModelMetricsPanel({
  comparisonRows,
  modelReports
}: ModelMetricsPanelProps) {
  return (
    <>
      <section className="result-panel">
        <h2>Model Comparison</h2>
        {comparisonRows.length === 0 ? (
          <p>No comparison rows available.</p>
        ) : (
          <table className="data-table">
            <thead>
              <tr>
                <th>Model</th>
                <th>Family</th>
                <th>Primary Metric</th>
                <th>Validation</th>
                <th>Test</th>
              </tr>
            </thead>
            <tbody>
              {comparisonRows.map((row) => (
                <tr key={row.model_id}>
                  <td>{row.model_id}</td>
                  <td>{row.family}</td>
                  <td>{row.primary_metric_name}</td>
                  <td>
                    {row.validation_value === null || row.validation_value === undefined
                      ? "n/a"
                      : row.validation_value.toFixed(4)}
                  </td>
                  <td>
                    {row.test_value === null || row.test_value === undefined
                      ? "n/a"
                      : row.test_value.toFixed(4)}
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        )}
      </section>

      <section className="result-panel">
        <h2>Per-Model Split Metrics</h2>
        {modelReports.length === 0 ? (
          <p>No model reports available.</p>
        ) : (
          modelReports.map((report) => (
            <article className="nested-panel" key={report.model_id}>
              <h3>{report.model_id}</h3>
              {report.skipped ? (
                <p>Skipped: {report.skip_reason ?? "unavailable"}</p>
              ) : (
                <table className="data-table compact">
                  <thead>
                    <tr>
                      <th>Metric</th>
                      <th>Train</th>
                      <th>Validation</th>
                      <th>Test</th>
                    </tr>
                  </thead>
                  <tbody>
                    {metricKeys(report).map((key) => (
                      <tr key={`${report.model_id}-${key}`}>
                        <td>{key}</td>
                        <td>{formatMetric(report.metrics_by_split.train?.[key])}</td>
                        <td>{formatMetric(report.metrics_by_split.validation?.[key])}</td>
                        <td>{formatMetric(report.metrics_by_split.test?.[key])}</td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              )}
            </article>
          ))
        )}
      </section>
    </>
  );
}
