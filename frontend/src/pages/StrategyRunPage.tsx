import { useEffect, useState } from "react";
import { Link } from "react-router-dom";

import { ErrorAlert } from "../components/common/ErrorAlert";
import { LoadingState } from "../components/common/LoadingState";
import { StrategyRunForm } from "../components/forms/StrategyRunForm";
import { RunSummaryPanel } from "../components/results/RunSummaryPanel";
import { StepResultsTable } from "../components/results/StepResultsTable";
import { fetchCapabilities } from "../lib/api/metadata";
import { createStrategyRun } from "../lib/api/research";
import type { RunSummaryResponse, StrategyRunRequest } from "../lib/api/types";

export function StrategyRunPage() {
  const [providers, setProviders] = useState<string[]>([]);
  const [result, setResult] = useState<RunSummaryResponse | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<unknown>(null);

  useEffect(() => {
    async function loadProviders() {
      try {
        const capabilities = await fetchCapabilities();
        setProviders(capabilities.providers);
      } catch {
        setProviders([]);
      }
    }
    void loadProviders();
  }, []);

  async function submit(payload: StrategyRunRequest) {
    setLoading(true);
    setError(null);
    setResult(null);
    try {
      const response = await createStrategyRun(payload);
      setResult(response);
    } catch (err) {
      setError(err);
    } finally {
      setLoading(false);
    }
  }

  return (
    <section className="page">
      <h2>Strategy Research Run</h2>
      <p>Submit strategy research payloads directly to the backend API.</p>
      <StrategyRunForm
        providers={providers}
        isSubmitting={loading}
        onSubmit={submit}
      />

      {loading ? <LoadingState label="Running strategy workflow..." /> : null}
      {error ? <ErrorAlert error={error} /> : null}
      {result ? (
        <>
          <section className="result-panel">
            <h2>Next Step</h2>
            <p>
              <Link to={`/runs/${encodeURIComponent(result.run_id)}/strategy`}>
                Open Strategy Detail Page
              </Link>
            </p>
          </section>
          <RunSummaryPanel result={result} />
          <StepResultsTable steps={result.step_results} />
        </>
      ) : null}
    </section>
  );
}
