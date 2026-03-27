import { useEffect, useMemo, useState } from "react";
import { Link, useNavigate } from "react-router-dom";

import { ErrorAlert } from "../components/common/ErrorAlert";
import { LoadingState } from "../components/common/LoadingState";
import { RunHistoryFilters } from "../components/history/RunHistoryFilters";
import { RunHistoryTable } from "../components/history/RunHistoryTable";
import { fetchRunHistory, type HistoryListQuery } from "../lib/history/api";
import type { RunHistoryItem } from "../lib/history/types";

const DEFAULT_QUERY: HistoryListQuery = {
  limit: 50,
  offset: 0,
  sort: "started_desc"
};

export function RunHistoryPage() {
  const navigate = useNavigate();
  const [queryDraft, setQueryDraft] = useState<HistoryListQuery>(DEFAULT_QUERY);
  const [query, setQuery] = useState<HistoryListQuery>(DEFAULT_QUERY);
  const [runs, setRuns] = useState<RunHistoryItem[]>([]);
  const [selectedIds, setSelectedIds] = useState<string[]>([]);
  const [warnings, setWarnings] = useState<string[]>([]);
  const [total, setTotal] = useState(0);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<unknown>(null);

  useEffect(() => {
    async function load() {
      setLoading(true);
      setError(null);
      try {
        const response = await fetchRunHistory(query);
        setRuns(response.items);
        setWarnings(response.warnings);
        setTotal(response.total);
        setSelectedIds((prev) => prev.filter((id) => response.items.some((run) => run.run_id === id)));
      } catch (err) {
        setError(err);
        setRuns([]);
        setWarnings([]);
        setTotal(0);
      } finally {
        setLoading(false);
      }
    }
    void load();
  }, [query]);

  function toggleSelected(runId: string) {
    setSelectedIds((prev) =>
      prev.includes(runId) ? prev.filter((value) => value !== runId) : [...prev, runId]
    );
  }

  function resetFilters() {
    setQueryDraft(DEFAULT_QUERY);
    setQuery(DEFAULT_QUERY);
  }

  const selectedSummary = useMemo(
    () => runs.filter((run) => selectedIds.includes(run.run_id)),
    [runs, selectedIds]
  );

  return (
    <section className="page">
      <h2>Run History</h2>
      <p>Browse persisted runs, reopen detail pages, and select runs for compare.</p>

      <RunHistoryFilters
        value={queryDraft}
        onChange={setQueryDraft}
        onApply={() => setQuery({ ...queryDraft, offset: 0 })}
        onReset={resetFilters}
        loading={loading}
      />

      <section className="result-panel">
        <h2>Actions</h2>
        <div className="controls-row">
          <button
            type="button"
            disabled={selectedIds.length < 2 || selectedIds.length > 5}
            onClick={() =>
              navigate(
                `/compare?ids=${encodeURIComponent(selectedIds.join(","))}&mode=auto`
              )
            }
          >
            Compare Selected ({selectedIds.length})
          </button>
          <Link to="/runs">Legacy Stored Runs View</Link>
          <span>Total matched: {total}</span>
        </div>
      </section>

      {loading ? <LoadingState label="Loading run history..." /> : null}
      {error ? <ErrorAlert error={error} /> : null}

      {warnings.length > 0 ? (
        <section className="result-panel">
          <h2>History Warnings</h2>
          <ul className="simple-list">
            {warnings.map((warning) => (
              <li key={warning}>{warning}</li>
            ))}
          </ul>
        </section>
      ) : null}

      <RunHistoryTable
        runs={runs}
        selectedIds={selectedIds}
        onToggleSelection={toggleSelected}
      />

      {selectedSummary.length > 0 ? (
        <section className="result-panel">
          <h2>Selected Runs</h2>
          <ul className="simple-list">
            {selectedSummary.map((run) => (
              <li key={run.run_id}>
                {run.run_id} ({run.workflow_type}, {run.status})
              </li>
            ))}
          </ul>
        </section>
      ) : null}
    </section>
  );
}
