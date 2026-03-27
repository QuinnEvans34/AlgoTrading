import { useEffect, useState } from "react";

import { ErrorAlert } from "../components/common/ErrorAlert";
import { LoadingState } from "../components/common/LoadingState";
import { LiveAttemptsTable } from "../components/live/LiveAttemptsTable";
import { LiveGuardrailPanel } from "../components/live/LiveGuardrailPanel";
import { LiveStatusPanel } from "../components/live/LiveStatusPanel";
import { ManualLiveOrderForm } from "../components/live/ManualLiveOrderForm";
import {
  fetchLiveExecutionAttempts,
  fetchLiveExecutionReadiness,
  submitManualLiveOrder,
  validateLiveTradeIntent
} from "../lib/liveExecution/api";
import type {
  LiveExecutionAttemptRecord,
  LiveExecutionReadinessResponse,
  LiveIntentValidationResponse,
  LiveTradeIntentRequest,
  ManualLiveOrderRequest,
  ManualLiveSubmitResponse
} from "../lib/liveExecution/types";

export function LiveExecutionPage() {
  const [readiness, setReadiness] = useState<LiveExecutionReadinessResponse | null>(
    null
  );
  const [attempts, setAttempts] = useState<LiveExecutionAttemptRecord[]>([]);
  const [validation, setValidation] = useState<LiveIntentValidationResponse | null>(
    null
  );
  const [submitResult, setSubmitResult] = useState<ManualLiveSubmitResponse | null>(
    null
  );
  const [loading, setLoading] = useState(false);
  const [submitting, setSubmitting] = useState(false);
  const [error, setError] = useState<unknown>(null);

  async function refresh() {
    setLoading(true);
    setError(null);
    try {
      const [readinessResponse, attemptsResponse] = await Promise.all([
        fetchLiveExecutionReadiness(),
        fetchLiveExecutionAttempts(25)
      ]);
      setReadiness(readinessResponse);
      setAttempts(attemptsResponse.attempts);
    } catch (err) {
      setError(err);
    } finally {
      setLoading(false);
    }
  }

  useEffect(() => {
    void refresh();
  }, []);

  async function onValidate(intent: LiveTradeIntentRequest) {
    setSubmitting(true);
    setError(null);
    setSubmitResult(null);
    try {
      const response = await validateLiveTradeIntent(intent);
      setValidation(response);
    } catch (err) {
      setError(err);
    } finally {
      setSubmitting(false);
    }
  }

  async function onSubmit(request: ManualLiveOrderRequest) {
    setSubmitting(true);
    setError(null);
    try {
      const response = await submitManualLiveOrder(request);
      setSubmitResult(response);
      await refresh();
    } catch (err) {
      setError(err);
    } finally {
      setSubmitting(false);
    }
  }

  return (
    <section className="page">
      <h2>Live Execution (Manual, Strictly Guarded)</h2>
      <p>
        Manual-only operator surface for guarded live-order attempts through the broker
        boundary. Live execution remains disabled by default.
      </p>

      <div className="controls-row">
        <button type="button" onClick={() => void refresh()} disabled={loading}>
          {loading ? "Refreshing..." : "Refresh Live Readiness"}
        </button>
      </div>

      {loading ? <LoadingState label="Loading live execution state..." /> : null}
      {error ? <ErrorAlert error={error} /> : null}

      <LiveStatusPanel readiness={readiness} />
      <LiveGuardrailPanel readiness={readiness} />

      <ManualLiveOrderForm
        readiness={readiness}
        submitting={submitting}
        onValidate={onValidate}
        onSubmit={onSubmit}
      />

      {validation ? (
        <section className="result-panel">
          <h3>Intent Validation</h3>
          <div className="info-item">
            <span>Accepted</span>
            <strong>{validation.accepted ? "Yes" : "No"}</strong>
          </div>
          {validation.reasons.length > 0 ? (
            <ul className="simple-list">
              {validation.reasons.map((reason) => (
                <li key={reason}>{reason}</li>
              ))}
            </ul>
          ) : null}
          <details className="nested-panel">
            <summary>Payload Preview</summary>
            <pre className="debug-json">
              {JSON.stringify(validation.broker_payload_preview ?? {}, null, 2)}
            </pre>
          </details>
        </section>
      ) : null}

      {submitResult ? (
        <section className="result-panel">
          <h3>Manual Submit Result</h3>
          <pre className="debug-json">{JSON.stringify(submitResult, null, 2)}</pre>
        </section>
      ) : null}

      <LiveAttemptsTable attempts={attempts} />
    </section>
  );
}
