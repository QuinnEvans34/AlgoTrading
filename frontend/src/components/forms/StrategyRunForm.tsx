import { useMemo, useState } from "react";

import { generateSampleCandles } from "../../lib/candles/sampleCandles";
import type { AssetClass, BarInterval, StrategyRunRequest } from "../../lib/api/types";
import {
  buildFetchSource,
  CandleSourceFields,
  type CandleSourceFormState
} from "./CandleSourceFields";

interface StrategyRunFormProps {
  providers: string[];
  isSubmitting: boolean;
  onSubmit: (payload: StrategyRunRequest) => Promise<void>;
}

function defaultDateTimeLocal(offsetDays: number): string {
  const now = new Date();
  now.setDate(now.getDate() + offsetDays);
  now.setMinutes(0, 0, 0);
  return `${now.getFullYear()}-${String(now.getMonth() + 1).padStart(2, "0")}-${String(
    now.getDate()
  ).padStart(2, "0")}T${String(now.getHours()).padStart(2, "0")}:00`;
}

export function StrategyRunForm({
  providers,
  isSubmitting,
  onSubmit
}: StrategyRunFormProps) {
  const [symbol, setSymbol] = useState("AAPL");
  const [assetClass, setAssetClass] = useState<AssetClass>("stock");
  const [interval, setInterval] = useState<BarInterval>("1d");
  const [warmupBars, setWarmupBars] = useState(80);
  const [minConfidence, setMinConfidence] = useState(0.1);
  const [persistSummary, setPersistSummary] = useState(true);
  const [runName, setRunName] = useState("");
  const [localError, setLocalError] = useState<string | null>(null);
  const [sourceState, setSourceState] = useState<CandleSourceFormState>({
    mode: "inline",
    providerName: providers[0] ?? "oanda",
    start: defaultDateTimeLocal(-60),
    end: defaultDateTimeLocal(0),
    limit: "",
    inlineBars: 220
  });

  const inlineCandles = useMemo(
    () => generateSampleCandles(sourceState.inlineBars),
    [sourceState.inlineBars]
  );

  async function handleSubmit(event: React.FormEvent<HTMLFormElement>) {
    event.preventDefault();
    setLocalError(null);

    if (!symbol.trim()) {
      setLocalError("Symbol is required.");
      return;
    }
    if (sourceState.mode === "fetch" && !sourceState.providerName.trim()) {
      setLocalError("Provider name is required for fetch mode.");
      return;
    }
    if (sourceState.mode === "fetch" && (!sourceState.start || !sourceState.end)) {
      setLocalError("Start and end datetimes are required for fetch mode.");
      return;
    }

    const payload: StrategyRunRequest = {
      instrument: {
        symbol: symbol.trim().toUpperCase(),
        asset_class: assetClass
      },
      interval,
      candle_source:
        sourceState.mode === "inline"
          ? {
              source_type: "inline_candles",
              candles: inlineCandles
            }
          : buildFetchSource(sourceState),
      strategy_spec: {
        strategy_id: "technical_rule_v1",
        backtest_config: {
          warmup_bars: warmupBars,
          min_signal_confidence: minConfidence
        }
      },
      run_config: {
        run_name: runName || undefined,
        persist_summary: persistSummary,
        strict_failures: true
      }
    };

    await onSubmit(payload);
  }

  return (
    <form className="run-form" onSubmit={handleSubmit}>
      <section className="form-section">
        <h3>Instrument</h3>
        <label className="field-inline">
          <span>Symbol</span>
          <input
            value={symbol}
            onChange={(event) => setSymbol(event.target.value)}
            placeholder="AAPL"
          />
        </label>
        <label className="field-inline">
          <span>Asset Class</span>
          <select
            value={assetClass}
            onChange={(event) => setAssetClass(event.target.value as AssetClass)}
          >
            <option value="stock">stock</option>
            <option value="forex">forex</option>
          </select>
        </label>
        <label className="field-inline">
          <span>Interval</span>
          <select
            value={interval}
            onChange={(event) => setInterval(event.target.value as BarInterval)}
          >
            <option value="1m">1m</option>
            <option value="5m">5m</option>
            <option value="15m">15m</option>
            <option value="30m">30m</option>
            <option value="1h">1h</option>
            <option value="4h">4h</option>
            <option value="1d">1d</option>
          </select>
        </label>
      </section>

      <CandleSourceFields
        value={sourceState}
        onChange={setSourceState}
        providers={providers}
      />

      <section className="form-section">
        <h3>Backtest Settings</h3>
        <label className="field-inline">
          <span>Warmup bars</span>
          <input
            type="number"
            min={0}
            value={warmupBars}
            onChange={(event) => setWarmupBars(Number(event.target.value))}
          />
        </label>
        <label className="field-inline">
          <span>Min confidence</span>
          <input
            type="number"
            min={0}
            max={1}
            step="0.01"
            value={minConfidence}
            onChange={(event) => setMinConfidence(Number(event.target.value))}
          />
        </label>
        <label className="field-inline">
          <span>Run name (optional)</span>
          <input
            value={runName}
            onChange={(event) => setRunName(event.target.value)}
            placeholder="strategy-aapl-v1"
          />
        </label>
        <label className="field-inline checkbox-row">
          <input
            type="checkbox"
            checked={persistSummary}
            onChange={(event) => setPersistSummary(event.target.checked)}
          />
          <span>Persist summary for Runs page</span>
        </label>
      </section>

      {localError ? <p className="local-error">{localError}</p> : null}

      <button type="submit" disabled={isSubmitting}>
        {isSubmitting ? "Running..." : "Run Strategy Research"}
      </button>
    </form>
  );
}

