import type { Candle } from "../api/types";

export function generateSampleCandles(count = 220): Candle[] {
  const candles: Candle[] = [];
  let price = 100;
  let timestamp = new Date(Date.UTC(2025, 0, 1, 0, 0, 0));

  for (let i = 0; i < count; i += 1) {
    const wave = Math.sin(i / 9) * 0.8;
    const drift = i < count * 0.6 ? 0.12 : -0.04;
    const noise = ((i * 17) % 10 - 5) * 0.05;
    const close = Math.max(1, price + drift + wave + noise);
    const high = Math.max(price, close) + 0.25;
    const low = Math.min(price, close) - 0.25;

    candles.push({
      timestamp: timestamp.toISOString(),
      open: Number(price.toFixed(5)),
      high: Number(high.toFixed(5)),
      low: Number(low.toFixed(5)),
      close: Number(close.toFixed(5)),
      volume: 1_000_000 + i * 1000
    });

    price = close;
    timestamp = new Date(timestamp.getTime() + 24 * 60 * 60 * 1000);
  }

  return candles;
}

