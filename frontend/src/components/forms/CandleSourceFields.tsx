import type { MarketDataFetchSource } from "../../lib/api/types";

export type CandleSourceMode = "inline" | "fetch";

export interface CandleSourceFormState {
  mode: CandleSourceMode;
  providerName: string;
  start: string;
  end: string;
  limit: string;
  inlineBars: number;
}

interface CandleSourceFieldsProps {
  value: CandleSourceFormState;
  onChange: (next: CandleSourceFormState) => void;
  providers: string[];
}

export function CandleSourceFields({
  value,
  onChange,
  providers
}: CandleSourceFieldsProps) {
  const defaultProvider = providers[0] ?? "oanda";

  return (
    <section className="form-section">
      <h3>Candle Source</h3>
      <label className="field-inline">
        <span>Mode</span>
        <select
          value={value.mode}
          onChange={(event) =>
            onChange({
              ...value,
              mode: event.target.value as CandleSourceMode,
              providerName: value.providerName || defaultProvider
            })
          }
        >
          <option value="inline">Inline sample candles</option>
          <option value="fetch">Fetch from provider</option>
        </select>
      </label>

      {value.mode === "inline" ? (
        <label className="field-inline">
          <span>Sample bars</span>
          <input
            type="number"
            min={120}
            max={5000}
            value={value.inlineBars}
            onChange={(event) =>
              onChange({
                ...value,
                inlineBars: Number(event.target.value)
              })
            }
          />
        </label>
      ) : (
        <>
          <label className="field-inline">
            <span>Provider</span>
            <input
              value={value.providerName}
              onChange={(event) =>
                onChange({
                  ...value,
                  providerName: event.target.value
                })
              }
              list="provider-list"
              placeholder={defaultProvider}
            />
            <datalist id="provider-list">
              {providers.map((provider) => (
                <option key={provider} value={provider} />
              ))}
            </datalist>
          </label>
          <label className="field-inline">
            <span>Start (UTC)</span>
            <input
              type="datetime-local"
              value={value.start}
              onChange={(event) => onChange({ ...value, start: event.target.value })}
            />
          </label>
          <label className="field-inline">
            <span>End (UTC)</span>
            <input
              type="datetime-local"
              value={value.end}
              onChange={(event) => onChange({ ...value, end: event.target.value })}
            />
          </label>
          <label className="field-inline">
            <span>Limit (optional)</span>
            <input
              type="number"
              min={1}
              value={value.limit}
              onChange={(event) => onChange({ ...value, limit: event.target.value })}
            />
          </label>
        </>
      )}
    </section>
  );
}

function asUtcIso(datetimeLocal: string): string {
  return new Date(datetimeLocal).toISOString();
}

export function buildFetchSource(
  value: CandleSourceFormState
): MarketDataFetchSource {
  return {
    source_type: "market_data_fetch",
    provider_name: value.providerName.trim(),
    start: asUtcIso(value.start),
    end: asUtcIso(value.end),
    ...(value.limit.trim() ? { limit: Number(value.limit) } : {})
  };
}

