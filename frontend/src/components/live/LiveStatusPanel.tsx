import type { LiveExecutionReadinessResponse } from "../../lib/liveExecution/types";

interface LiveStatusPanelProps {
  readiness: LiveExecutionReadinessResponse | null;
}

export function LiveStatusPanel({ readiness }: LiveStatusPanelProps) {
  if (!readiness) {
    return null;
  }
  return (
    <section className="result-panel">
      <h3>Live Readiness</h3>
      <div className="summary-grid">
        <div className="info-item">
          <span>Broker</span>
          <strong>{readiness.broker_name}</strong>
        </div>
        <div className="info-item">
          <span>State</span>
          <strong>{readiness.state}</strong>
        </div>
        <div className="info-item">
          <span>Enabled</span>
          <strong>{readiness.enabled ? "Yes" : "No"}</strong>
        </div>
        <div className="info-item">
          <span>Configured</span>
          <strong>{readiness.configured ? "Yes" : "No"}</strong>
        </div>
        <div className="info-item">
          <span>Submission Allowed</span>
          <strong>{readiness.submission_allowed ? "Yes" : "No"}</strong>
        </div>
        <div className="info-item">
          <span>Manual Submit Ready</span>
          <strong>{readiness.manual_submission_ready ? "Yes" : "No"}</strong>
        </div>
      </div>
      <p>{readiness.message}</p>
    </section>
  );
}
