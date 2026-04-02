import { useEffect, useMemo, useState } from "react";
import { Link, useSearchParams } from "react-router-dom";

import { ErrorAlert } from "../components/common/ErrorAlert";
import { LoadingState } from "../components/common/LoadingState";
import { CompareMetricCards } from "../components/compare/CompareMetricCards";
import { CompareSummaryTable } from "../components/compare/CompareSummaryTable";
import { RecentComparePanel } from "../components/workflow/RecentComparePanel";
import { compareRuns } from "../lib/history/api";
import type { CompareMode, CompareRunsResponse } from "../lib/history/types";
import {
  fetchRecentCompares,
  touchRecentCompare
} from "../lib/workflow/api";
import type { RecentCompareSet } from "../lib/workflow/types";

function parseIds(raw: string | null): string[] {
  if (!raw) {
    return [];
  }
  return raw
    .split(",")
    .map((value) => value.trim())
    .filter((value) => value.length > 0);
}

export function CompareRunsPage() {
  const [searchParams, setSearchParams] = useSearchParams();
  const [result, setResult] = useState<CompareRunsResponse | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<unknown>(null);
  const [recentCompares, setRecentCompares] = useState<RecentCompareSet[]>([]);
  const [recentCompareError, setRecentCompareError] = useState<unknown>(null);

  const ids = useMemo(() => parseIds(searchParams.get("ids")), [searchParams]);
  const mode = (searchParams.get("mode") as CompareMode | null) ?? "auto";

  useEffect(() => {
    async function loadRecentCompares() {
      try {
        const response = await fetchRecentCompares();
        setRecentCompares(response.items);
      } catch (err) {
        setRecentCompareError(err);
      }
    }
    void loadRecentCompares();
  }, []);

  useEffect(() => {
    async function load() {
      if (ids.length < 2) {
        setResult(null);
        return;
      }
      setLoading(true);
      setError(null);
      try {
        const response = await compareRuns({ run_ids: ids, mode });
        setResult(response);
        try {
          await touchRecentCompare({ compare_mode: mode, run_ids: ids });
          const recent = await fetchRecentCompares();
          setRecentCompares(recent.items);
        } catch {
          // Keep compare rendering stable even if recents persistence fails.
        }
      } catch (err) {
        setError(err);
        setResult(null);
      } finally {
        setLoading(false);
      }
    }
    void load();
  }, [ids, mode]);

  function useRecentCompare(item: RecentCompareSet) {
    setSearchParams(
      {
        ids: item.run_ids.join(","),
        mode: item.compare_mode
      },
      { replace: true }
    );
  }

  return (
    <section className="page">
      <h2>Compare Runs</h2>
      <p>Compare 2-5 compatible saved runs.</p>

      {recentCompareError ? <ErrorAlert error={recentCompareError} /> : null}
      <RecentComparePanel
        items={recentCompares}
        busy={loading}
        onUse={useRecentCompare}
      />

      <section className="result-panel">
        <h2>Selection</h2>
        <div className="field-inline compact">
          <span>Run IDs (CSV)</span>
          <input
            aria-label="Run IDs (CSV)"
            value={ids.join(",")}
            onChange={(event) =>
              setSearchParams({ ids: event.target.value, mode }, { replace: true })
            }
            placeholder="run-id-1,run-id-2"
          />
        </div>
        <div className="field-inline compact">
          <span>Mode</span>
          <select
            aria-label="Compare mode"
            value={mode}
            onChange={(event) =>
              setSearchParams(
                { ids: ids.join(","), mode: event.target.value as CompareMode },
                { replace: true }
              )
            }
          >
            <option value="auto">auto</option>
            <option value="strategy">strategy</option>
            <option value="ml">ml</option>
          </select>
        </div>
        <div className="controls-row">
          <Link to="/history">Back to Run History</Link>
        </div>
      </section>

      {loading ? <LoadingState label="Comparing selected runs..." /> : null}
      {error ? <ErrorAlert error={error} /> : null}

      {result ? (
        <>
          <section className="result-panel">
            <h2>Compare Mode</h2>
            <p>{result.mode}</p>
          </section>
          {result.warnings.length > 0 ? (
            <section className="result-panel">
              <h2>Warnings</h2>
              <ul className="simple-list">
                {result.warnings.map((warning) => (
                  <li key={warning}>{warning}</li>
                ))}
              </ul>
            </section>
          ) : null}
          <CompareMetricCards cards={result.cards} />
          <CompareSummaryTable rows={result.rows} />
        </>
      ) : null}

      {!loading && !result && ids.length < 2 ? (
        <section className="result-panel">
          <p>Select at least two run IDs to compare.</p>
        </section>
      ) : null}
    </section>
  );
}
