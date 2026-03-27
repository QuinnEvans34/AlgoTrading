import { useMemo, useState } from "react";

import { generateSampleCandles } from "../../lib/candles/sampleCandles";
import type { AssetClass, BarInterval, MLRunRequest } from "../../lib/api/types";
import {
  buildFetchSource,
  CandleSourceFields,
  type CandleSourceFormState
} from "./CandleSourceFields";

interface MLRunFormProps {
  providers: string[];
  isSubmitting: boolean;
  onSubmit: (payload: MLRunRequest) => Promise<void>;
}

function defaultDateTimeLocal(offsetDays: number): string {
  const now = new Date();
  now.setDate(now.getDate() + offsetDays);
  now.setMinutes(0, 0, 0);
  return `${now.getFullYear()}-${String(now.getMonth() + 1).padStart(2, "0")}-${String(
    now.getDate()
  ).padStart(2, "0")}T${String(now.getHours()).padStart(2, "0")}:00`;
}

export function MLRunForm({ providers, isSubmitting, onSubmit }: MLRunFormProps) {
  const [symbol, setSymbol] = useState("AAPL");
  const [assetClass, setAssetClass] = useState<AssetClass>("stock");
  const [interval, setInterval] = useState<BarInterval>("1d");
  const [horizonBars, setHorizonBars] = useState(5);
  const [taskType, setTaskType] = useState<"classification" | "regression">(
    "classification"
  );
  const [persistSummary, setPersistSummary] = useState(true);
  const [runName, setRunName] = useState("");
  const [localError, setLocalError] = useState<string | null>(null);
  const [sourceState, setSourceState] = useState<CandleSourceFormState>({
    mode: "inline",
    providerName: providers[0] ?? "oanda",
    start: defaultDateTimeLocal(-120),
    end: defaultDateTimeLocal(0),
    limit: "",
    inlineBars: 260
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

    const returnLabel = `ret_h${horizonBars}`;
    const directionLabel = `dir_h${horizonBars}`;
    const payload: MLRunRequest = {
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
      ml_spec: {
        task_type: taskType,
        label_specs:
          taskType === "classification"
            ? [
                {
                  label_type: "future_return",
                  horizon_bars: horizonBars,
                  name: returnLabel
                },
                {
                  label_type: "direction",
                  horizon_bars: horizonBars,
                  name: directionLabel
                }
              ]
            : [
                {
                  label_type: "future_return",
                  horizon_bars: horizonBars,
                  name: returnLabel
                }
              ],
        target_label: taskType === "classification" ? directionLabel : returnLabel,
        model_specs:
          taskType === "classification"
            ? [{ model_id: "dummy_cls", family: "dummy_classifier" }]
            : [{ model_id: "dummy_reg", family: "dummy_regressor" }]
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
        <h3>ML Settings</h3>
        <label className="field-inline">
          <span>Task Type</span>
          <select
            value={taskType}
            onChange={(event) =>
              setTaskType(event.target.value as "classification" | "regression")
            }
          >
            <option value="classification">classification</option>
            <option value="regression">regression</option>
          </select>
        </label>
        <label className="field-inline">
          <span>Horizon Bars</span>
          <input
            type="number"
            min={1}
            max={120}
            value={horizonBars}
            onChange={(event) => setHorizonBars(Number(event.target.value))}
          />
        </label>
        <label className="field-inline">
          <span>Run name (optional)</span>
          <input
            value={runName}
            onChange={(event) => setRunName(event.target.value)}
            placeholder="ml-aapl-h5"
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
        {isSubmitting ? "Running..." : "Run ML Research"}
      </button>
    </form>
  );
}

