import type { HistoryListQuery } from "../../lib/history/api";

interface RunHistoryFiltersProps {
  value: HistoryListQuery;
  onChange: (next: HistoryListQuery) => void;
  onApply: () => void;
  onReset: () => void;
  loading: boolean;
}

export function RunHistoryFilters({
  value,
  onChange,
  onApply,
  onReset,
  loading
}: RunHistoryFiltersProps) {
  return (
    <section className="result-panel">
      <h2>Filters</h2>
      <div className="filters-grid">
        <label className="field-inline compact">
          <span>Workflow</span>
          <select
            value={value.workflow_type ?? ""}
            onChange={(event) =>
              onChange({ ...value, workflow_type: event.target.value || undefined })
            }
          >
            <option value="">all</option>
            <option value="strategy_research">strategy_research</option>
            <option value="ml_research">ml_research</option>
            <option value="hybrid_research">hybrid_research</option>
          </select>
        </label>

        <label className="field-inline compact">
          <span>Status</span>
          <select
            value={value.status ?? ""}
            onChange={(event) =>
              onChange({ ...value, status: event.target.value || undefined })
            }
          >
            <option value="">all</option>
            <option value="success">success</option>
            <option value="partial_failure">partial_failure</option>
            <option value="failed">failed</option>
          </select>
        </label>

        <label className="field-inline compact">
          <span>Search</span>
          <input
            value={value.q ?? ""}
            onChange={(event) => onChange({ ...value, q: event.target.value || undefined })}
            placeholder="run id, name, symbol"
          />
        </label>

        <label className="field-inline compact">
          <span>Sort</span>
          <select
            value={value.sort ?? "started_desc"}
            onChange={(event) =>
              onChange({
                ...value,
                sort: (event.target.value as "started_desc" | "started_asc") ?? "started_desc"
              })
            }
          >
            <option value="started_desc">started desc</option>
            <option value="started_asc">started asc</option>
          </select>
        </label>

        <label className="field-inline compact">
          <span>Limit</span>
          <input
            type="number"
            min={1}
            max={500}
            value={value.limit ?? 50}
            onChange={(event) =>
              onChange({ ...value, limit: Math.max(1, Number(event.target.value || "50")) })
            }
          />
        </label>
      </div>

      <div className="controls-row">
        <button type="button" disabled={loading} onClick={onApply}>
          {loading ? "Loading..." : "Apply"}
        </button>
        <button type="button" disabled={loading} onClick={onReset}>
          Reset
        </button>
      </div>
    </section>
  );
}
