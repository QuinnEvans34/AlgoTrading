import type { LiveSafetyStatus } from "../../lib/settings/types";

interface LiveSafetyPanelProps {
  safety: LiveSafetyStatus;
}

export function LiveSafetyPanel({ safety }: LiveSafetyPanelProps) {
  return (
    <section className="result-panel">
      <h3>Live Execution Safety</h3>
      <div className="summary-grid">
        <div className="info-item">
          <span>Broker</span>
          <strong>{safety.broker_name}</strong>
        </div>
        <div className="info-item">
          <span>Enabled</span>
          <strong>{safety.enabled ? "Yes" : "No"}</strong>
        </div>
        <div className="info-item">
          <span>Allow Order Submission</span>
          <strong>{safety.allow_order_submission ? "Yes" : "No"}</strong>
        </div>
        <div className="info-item">
          <span>Submit Feature Enabled</span>
          <strong>{safety.submit_feature_enabled ? "Yes" : "No"}</strong>
        </div>
        <div className="info-item">
          <span>Effective Submission Enabled</span>
          <strong>{safety.effective_submission_enabled ? "Yes" : "No"}</strong>
        </div>
        <div className="info-item">
          <span>Credentials Configured</span>
          <strong>{safety.credentials_configured ? "Yes" : "No"}</strong>
        </div>
        <div className="info-item">
          <span>Environment</span>
          <strong>{safety.environment}</strong>
        </div>
        <div className="info-item">
          <span>Timeout (seconds)</span>
          <strong>{safety.request_timeout_seconds}</strong>
        </div>
        <div className="info-item">
          <span>Confirmation Phrase</span>
          <strong>{safety.confirmation_phrase}</strong>
        </div>
        <div className="info-item">
          <span>Attempt Log Path</span>
          <strong>{safety.attempt_log_path}</strong>
        </div>
      </div>
    </section>
  );
}
