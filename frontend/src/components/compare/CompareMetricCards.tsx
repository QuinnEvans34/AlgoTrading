import type { CompareMetricCard } from "../../lib/history/types";

interface CompareMetricCardsProps {
  cards: CompareMetricCard[];
}

export function CompareMetricCards({ cards }: CompareMetricCardsProps) {
  if (cards.length === 0) {
    return null;
  }
  return (
    <section className="result-panel">
      <h2>Compare Highlights</h2>
      <div className="metrics-grid">
        {cards.map((card) => (
          <div className="metric-card" key={card.label}>
            <span className="metric-label">{card.label}</span>
            <strong className="metric-value">
              best: {card.best_run_id ?? "n/a"}{" "}
              {card.best_value === null || card.best_value === undefined
                ? ""
                : `(${card.best_value.toFixed(4)})`}
            </strong>
            <span className="metric-label">
              worst: {card.worst_run_id ?? "n/a"}{" "}
              {card.worst_value === null || card.worst_value === undefined
                ? ""
                : `(${card.worst_value.toFixed(4)})`}
            </span>
          </div>
        ))}
      </div>
    </section>
  );
}
