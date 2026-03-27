import { Link } from "react-router-dom";

import type { RunHistoryItem } from "../../lib/history/types";

interface RunHistoryTableProps {
  runs: RunHistoryItem[];
  selectedIds: string[];
  onToggleSelection: (runId: string) => void;
}

export function RunHistoryTable({
  runs,
  selectedIds,
  onToggleSelection
}: RunHistoryTableProps) {
  if (runs.length === 0) {
    return (
      <section className="result-panel">
        <h2>Run History</h2>
        <p>No saved runs matched your filters.</p>
      </section>
    );
  }

  return (
    <section className="result-panel">
      <h2>Run History</h2>
      <table className="data-table">
        <thead>
          <tr>
            <th>Select</th>
            <th>Run ID</th>
            <th>Workflow</th>
            <th>Status</th>
            <th>Symbol</th>
            <th>Interval</th>
            <th>Started</th>
            <th>Open</th>
          </tr>
        </thead>
        <tbody>
          {runs.map((run) => {
            const checked = selectedIds.includes(run.run_id);
            return (
              <tr key={run.run_id}>
                <td>
                  <input
                    type="checkbox"
                    checked={checked}
                    onChange={() => onToggleSelection(run.run_id)}
                  />
                </td>
                <td>{run.run_id}</td>
                <td>{run.workflow_type}</td>
                <td>{run.status}</td>
                <td>{run.instrument_symbol}</td>
                <td>{run.interval ?? "n/a"}</td>
                <td>
                  {run.started_at
                    ? new Date(run.started_at).toLocaleString()
                    : "n/a"}
                </td>
                <td>
                  {run.has_strategy ? (
                    <Link to={`/runs/${encodeURIComponent(run.run_id)}/strategy`}>
                      Strategy
                    </Link>
                  ) : null}
                  {run.has_strategy && run.has_ml ? " | " : null}
                  {run.has_ml ? (
                    <Link to={`/runs/${encodeURIComponent(run.run_id)}/ml`}>ML</Link>
                  ) : null}
                </td>
              </tr>
            );
          })}
        </tbody>
      </table>
    </section>
  );
}
