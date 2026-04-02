import type { Candle } from "../../lib/api/types";

interface PricePreviewChartProps {
  title: string;
  candles: Candle[];
}

function buildPolylinePoints(candles: Candle[], width: number, height: number): string {
  if (candles.length === 0) {
    return "";
  }
  if (candles.length === 1) {
    return `0,${height / 2} ${width},${height / 2}`;
  }
  const closes = candles.map((candle) => candle.close);
  const min = Math.min(...closes);
  const max = Math.max(...closes);
  const span = Math.max(max - min, 1e-9);
  return candles
    .map((candle, index) => {
      const x = (index / (candles.length - 1)) * width;
      const normalized = (candle.close - min) / span;
      const y = height - normalized * height;
      return `${x.toFixed(2)},${y.toFixed(2)}`;
    })
    .join(" ");
}

export function PricePreviewChart({ title, candles }: PricePreviewChartProps) {
  if (candles.length === 0) {
    return (
      <section className="result-panel">
        <h2>{title}</h2>
        <p>No preview candles are available.</p>
      </section>
    );
  }

  const width = 900;
  const height = 240;
  return (
    <section className="result-panel">
      <h2>{title}</h2>
      <svg
        className="line-chart"
        viewBox={`0 0 ${width} ${height}`}
        role="img"
        aria-label={`${title} chart`}
      >
        <polyline
          fill="none"
          stroke="var(--accent)"
          strokeWidth="2.5"
          points={buildPolylinePoints(candles, width, height)}
        />
      </svg>
    </section>
  );
}
