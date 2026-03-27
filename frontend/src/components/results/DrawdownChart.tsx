import type { ChartPoint } from "../../lib/results/types";

interface DrawdownChartProps {
  points: ChartPoint[];
}

function buildPolylinePoints(points: ChartPoint[], width: number, height: number): string {
  if (points.length === 0) {
    return "";
  }
  if (points.length === 1) {
    return `0,0 ${width},0`;
  }
  const min = Math.min(...points.map((point) => point.value), 0);
  const max = 0;
  const span = Math.max(max - min, 1e-9);
  return points
    .map((point, index) => {
      const x = (index / (points.length - 1)) * width;
      const normalized = (point.value - min) / span;
      const y = height - normalized * height;
      return `${x.toFixed(2)},${y.toFixed(2)}`;
    })
    .join(" ");
}

export function DrawdownChart({ points }: DrawdownChartProps) {
  if (points.length === 0) {
    return (
      <section className="result-panel">
        <h2>Drawdown Curve</h2>
        <p>No drawdown data available for this run.</p>
      </section>
    );
  }

  const width = 900;
  const height = 220;
  return (
    <section className="result-panel">
      <h2>Drawdown Curve</h2>
      <svg className="line-chart" viewBox={`0 0 ${width} ${height}`} role="img" aria-label="Drawdown curve">
        <polyline
          fill="none"
          stroke="var(--danger)"
          strokeWidth="2.5"
          points={buildPolylinePoints(points, width, height)}
        />
      </svg>
    </section>
  );
}
