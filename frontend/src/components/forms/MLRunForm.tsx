import { useState } from "react";

import type { MLRunRequest } from "../../lib/api/types";
import { mlDraftToRunRequest, type MLConfigDraft } from "../../lib/workflow/drafts";
import { CandleSourceFields } from "./CandleSourceFields";

interface MLRunFormProps {
  providers: string[];
  draft: MLConfigDraft;
  onChange: (next: MLConfigDraft) => void;
  isSubmitting: boolean;
  onSubmit: (payload: MLRunRequest) => Promise<void>;
}

export function MLRunForm({
  providers,
  draft,
  onChange,
  isSubmitting,
  onSubmit
}: MLRunFormProps) {
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

    await onSubmit(mlDraftToRunRequest(draft));
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
              onChange({ ...draft, assetClass: event.target.value as MLConfigDraft["assetClass"] })
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
              onChange({ ...draft, interval: event.target.value as MLConfigDraft["interval"] })
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
        <h3>ML Settings</h3>
        <label className="field-inline">
          <span>Task Type</span>
          <select
            value={draft.taskType}
            onChange={(event) =>
              onChange({
                ...draft,
                taskType: event.target.value as MLConfigDraft["taskType"]
              })
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
            value={draft.horizonBars}
            onChange={(event) =>
              onChange({ ...draft, horizonBars: Number(event.target.value) })
            }
          />
        </label>
        <label className="field-inline">
          <span>Run name (optional)</span>
          <input
            value={draft.runName}
            onChange={(event) => onChange({ ...draft, runName: event.target.value })}
            placeholder="ml-aapl-h5"
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
        {isSubmitting ? "Running..." : "Run ML Research"}
      </button>
    </form>
  );
}
