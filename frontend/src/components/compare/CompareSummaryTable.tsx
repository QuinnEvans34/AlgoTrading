interface CompareSummaryTableProps {
  rows: Array<Record<string, unknown>>;
}

function keysFromRows(rows: Array<Record<string, unknown>>): string[] {
  const set = new Set<string>();
  rows.forEach((row) => {
    Object.keys(row).forEach((key) => set.add(key));
  });
  const keys = Array.from(set);
  const preferred = [
    "run_id",
    "run_name",
    "workflow_type",
    "status",
    "instrument_symbol",
    "interval"
  ];
  const left = preferred.filter((key) => keys.includes(key));
  const right = keys.filter((key) => !preferred.includes(key)).sort();
  return [...left, ...right];
}

function formatValue(value: unknown): string {
  if (value === null || value === undefined) {
    return "n/a";
  }
  if (typeof value === "number") {
    return Number.isInteger(value) ? String(value) : value.toFixed(4);
  }
  return String(value);
}

export function CompareSummaryTable({ rows }: CompareSummaryTableProps) {
  if (rows.length === 0) {
    return (
      <section className="result-panel">
        <h2>Compare Table</h2>
        <p>No rows returned.</p>
      </section>
    );
  }
  const columns = keysFromRows(rows);
  return (
    <section className="result-panel">
      <h2>Compare Table</h2>
      <table className="data-table">
        <thead>
          <tr>
            {columns.map((column) => (
              <th key={column}>{column}</th>
            ))}
          </tr>
        </thead>
        <tbody>
          {rows.map((row) => (
            <tr key={String(row.run_id ?? JSON.stringify(row))}>
              {columns.map((column) => (
                <td key={`${String(row.run_id)}-${column}`}>
                  {formatValue(row[column])}
                </td>
              ))}
            </tr>
          ))}
        </tbody>
      </table>
    </section>
  );
}
