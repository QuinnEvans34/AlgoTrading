import type { RecentCompareSet } from "../../lib/workflow/types";

interface RecentComparePanelProps {
  items: RecentCompareSet[];
  busy: boolean;
  onUse: (item: RecentCompareSet) => void;
}

export function RecentComparePanel({
  items,
  busy,
  onUse
}: RecentComparePanelProps) {
  return (
    <section className="result-panel">
      <h2>Recent Compares</h2>
      {items.length === 0 ? (
        <p>No recent compare selections yet.</p>
      ) : (
        <ul className="simple-list">
          {items.map((item) => (
            <li key={item.id}>
              <strong>{item.compare_mode}</strong>: {item.run_ids.join(", ")}
              <div className="controls-row">
                <button type="button" disabled={busy} onClick={() => onUse(item)}>
                  Reuse Selection
                </button>
              </div>
            </li>
          ))}
        </ul>
      )}
    </section>
  );
}
