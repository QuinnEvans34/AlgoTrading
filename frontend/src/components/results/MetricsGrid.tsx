import type { MetricItem } from "../../lib/results/types";
import { MetricCard } from "./MetricCard";

interface MetricsGridProps {
  title: string;
  metrics: MetricItem[];
}

export function MetricsGrid({ title, metrics }: MetricsGridProps) {
  return (
    <section className="result-panel">
      <h2>{title}</h2>
      <div className="metrics-grid">
        {metrics.map((metric) => (
          <MetricCard
            key={metric.label}
            label={metric.label}
            value={metric.value}
          />
        ))}
      </div>
    </section>
  );
}
