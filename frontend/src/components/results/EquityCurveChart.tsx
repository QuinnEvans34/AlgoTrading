import type { ChartPoint } from "../../lib/results/types";

interface EquityCurveChartProps {
  points: ChartPoint[];
}

function buildPolylinePoints(points: ChartPoint[], width: number, height: number): string {
  if (points.length === 0) {
    return "";
  }
  if (points.length === 1) {
    return `0,${height / 2} ${width},${height / 2}`;
  }
  const values = points.map((point) => point.value);
  const min = Math.min(...values);
  const max = Math.max(...values);
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

export function EquityCurveChart({ points }: EquityCurveChartProps) {
  if (points.length === 0) {
    return (
      <section className="result-panel">
        <h2>Equity Curve</h2>
        <p>No equity data available for this run.</p>
      </section>
    );
  }

  const width = 900;
  const height = 260;
  return (
    <section className="result-panel">
      <h2>Equity Curve</h2>
      <svg className="line-chart" viewBox={`0 0 ${width} ${height}`} role="img" aria-label="Equity curve">
        <polyline
          fill="none"
          stroke="var(--accent)"
          strokeWidth="2.5"
          points={buildPolylinePoints(points, width, height)}
        />
      </svg>
    </section>
  );
}
