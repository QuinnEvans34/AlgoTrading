import { useState } from "react";

import type { StrategyRunRequest } from "../../lib/api/types";
import {
  strategyDraftToRunRequest,
  type StrategyConfigDraft
} from "../../lib/workflow/drafts";
import { CandleSourceFields } from "./CandleSourceFields";

interface StrategyRunFormProps {
  providers: string[];
  draft: StrategyConfigDraft;
  onChange: (next: StrategyConfigDraft) => void;
  isSubmitting: boolean;
  onSubmit: (payload: StrategyRunRequest) => Promise<void>;
}

export function StrategyRunForm({
  providers,
  draft,
  onChange,
  isSubmitting,
  onSubmit
}: StrategyRunFormProps) {
  const [localError, setLocalError] = useState<string | null>(null);

  async function handleSubmit(event: React.FormEvent<HTMLFormElement>) {
    event.preventDefault();
    setLocalError(null);

    if (!draft.symbol.trim()) {
      setLocalError("Symbol is required.");
      return;
    }
    if (draft.sourceState.mode === "fetch" && !draft.sourceState.providerName.trim()) {
      setLocalError("Provider name is required for fetch mode.");
      return;
    }
    if (
      draft.sourceState.mode === "fetch" &&
      (!draft.sourceState.start || !draft.sourceState.end)
    ) {
      setLocalError("Start and end datetimes are required for fetch mode.");
      return;
    }

    await onSubmit(strategyDraftToRunRequest(draft));
  }

  return (
    <form className="run-form" onSubmit={handleSubmit}>
      <section className="form-section">
        <h3>Instrument</h3>
        <label className="field-inline">
          <span>Symbol</span>
          <input
            value={draft.symbol}
            onChange={(event) => onChange({ ...draft, symbol: event.target.value })}
            placeholder="AAPL"
          />
        </label>
        <label className="field-inline">
          <span>Asset Class</span>
          <select
            value={draft.assetClass}
            onChange={(event) =>
              onChange({ ...draft, assetClass: event.target.value as StrategyConfigDraft["assetClass"] })
            }
          >
            <option value="stock">stock</option>
            <option value="forex">forex</option>
          </select>
        </label>
        <label className="field-inline">
          <span>Interval</span>
          <select
            value={draft.interval}
            onChange={(event) =>
              onChange({ ...draft, interval: event.target.value as StrategyConfigDraft["interval"] })
            }
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
        value={draft.sourceState}
        onChange={(sourceState) => onChange({ ...draft, sourceState })}
        providers={providers}
      />

      <section className="form-section">
        <h3>Backtest Settings</h3>
        <label className="field-inline">
          <span>Warmup bars</span>
          <input
            type="number"
            min={0}
            value={draft.warmupBars}
            onChange={(event) =>
              onChange({ ...draft, warmupBars: Number(event.target.value) })
            }
          />
        </label>
        <label className="field-inline">
          <span>Min confidence</span>
          <input
            type="number"
            min={0}
            max={1}
            step="0.01"
            value={draft.minConfidence}
            onChange={(event) =>
              onChange({ ...draft, minConfidence: Number(event.target.value) })
            }
          />
        </label>
        <label className="field-inline">
          <span>Run name (optional)</span>
          <input
            value={draft.runName}
            onChange={(event) => onChange({ ...draft, runName: event.target.value })}
            placeholder="strategy-aapl-v1"
          />
        </label>
        <label className="field-inline checkbox-row">
          <input
            type="checkbox"
            checked={draft.persistSummary}
            onChange={(event) =>
              onChange({ ...draft, persistSummary: event.target.checked })
            }
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
