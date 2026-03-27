import { useEffect, useState } from "react";

import { ErrorAlert } from "../components/common/ErrorAlert";
import { LoadingState } from "../components/common/LoadingState";
import { fetchHealth } from "../lib/api/health";
import type { HealthResponse } from "../lib/api/types";

export function HomePage() {
  const [health, setHealth] = useState<HealthResponse | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<unknown>(null);

  async function checkHealth() {
    setLoading(true);
    setError(null);
    try {
      const response = await fetchHealth();
      setHealth(response);
    } catch (err) {
      setError(err);
    } finally {
      setLoading(false);
    }
  }

  useEffect(() => {
    void checkHealth();
  }, []);

  return (
    <section className="page">
      <h2>Platform Status</h2>
      <p>
        This shell calls the backend API directly. Use this page to verify API
        connectivity before running research workflows.
      </p>
      <button type="button" onClick={() => void checkHealth()} disabled={loading}>
        {loading ? "Checking..." : "Refresh Health"}
      </button>

      {loading ? <LoadingState label="Checking backend health..." /> : null}
      {error ? <ErrorAlert error={error} /> : null}

      {health ? (
        <section className="result-panel">
          <h3>Health Response</h3>
          <div className="summary-grid">
            <div className="info-item">
              <span>Status</span>
              <strong>{health.status}</strong>
            </div>
            <div className="info-item">
              <span>Service</span>
              <strong>{health.service}</strong>
            </div>
            <div className="info-item">
              <span>Version</span>
              <strong>{health.version}</strong>
            </div>
            <div className="info-item">
              <span>Timestamp</span>
              <strong>{new Date(health.timestamp).toLocaleString()}</strong>
            </div>
          </div>
        </section>
      ) : null}
    </section>
  );
}

