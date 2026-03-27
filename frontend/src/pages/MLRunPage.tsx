import { useEffect, useState } from "react";
import { Link } from "react-router-dom";

import { ErrorAlert } from "../components/common/ErrorAlert";
import { LoadingState } from "../components/common/LoadingState";
import { MLRunForm } from "../components/forms/MLRunForm";
import { RunSummaryPanel } from "../components/results/RunSummaryPanel";
import { StepResultsTable } from "../components/results/StepResultsTable";
import { fetchCapabilities } from "../lib/api/metadata";
import { createMlRun } from "../lib/api/research";
import type { MLRunRequest, RunSummaryResponse } from "../lib/api/types";

export function MLRunPage() {
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

  async function submit(payload: MLRunRequest) {
    setLoading(true);
    setError(null);
    setResult(null);
    try {
      const response = await createMlRun(payload);
      setResult(response);
    } catch (err) {
      setError(err);
    } finally {
      setLoading(false);
    }
  }

  return (
    <section className="page">
      <h2>ML Research Run</h2>
      <p>Submit ML dataset + model run payloads to the backend orchestration API.</p>
      <MLRunForm providers={providers} isSubmitting={loading} onSubmit={submit} />

      {loading ? <LoadingState label="Running ML workflow..." /> : null}
      {error ? <ErrorAlert error={error} /> : null}
      {result ? (
        <>
          <section className="result-panel">
            <h2>Next Step</h2>
            <p>
              <Link to={`/runs/${encodeURIComponent(result.run_id)}/ml`}>
                Open ML Detail Page
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
