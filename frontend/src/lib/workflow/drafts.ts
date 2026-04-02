import { generateSampleCandles } from "../candles/sampleCandles";
import type {
  AssetClass,
  BarInterval,
  MLRunRequest,
  MarketDataFetchSource,
  StrategyRunRequest
} from "../api/types";
import type {
  SavedMLConfigPayload,
  SavedStrategyConfigPayload
} from "./types";

export type CandleSourceMode = "inline" | "fetch";

export interface CandleSourceDraftState {
  mode: CandleSourceMode;
  providerName: string;
  start: string;
  end: string;
  limit: string;
  inlineBars: number;
}

export interface StrategyConfigDraft {
  symbol: string;
  assetClass: AssetClass;
  interval: BarInterval;
  warmupBars: number;
  minConfidence: number;
  persistSummary: boolean;
  runName: string;
  sourceState: CandleSourceDraftState;
}

export interface MLConfigDraft {
  symbol: string;
  assetClass: AssetClass;
  interval: BarInterval;
  horizonBars: number;
  taskType: "classification" | "regression";
  persistSummary: boolean;
  runName: string;
  sourceState: CandleSourceDraftState;
}

export function defaultDateTimeLocal(offsetDays: number): string {
  const now = new Date();
  now.setDate(now.getDate() + offsetDays);
  now.setMinutes(0, 0, 0);
  return `${now.getFullYear()}-${String(now.getMonth() + 1).padStart(2, "0")}-${String(
    now.getDate()
  ).padStart(2, "0")}T${String(now.getHours()).padStart(2, "0")}:00`;
}

function asUtcIso(datetimeLocal: string): string {
  return new Date(datetimeLocal).toISOString();
}

function asDateTimeLocal(isoString: string): string {
  const value = new Date(isoString);
  const year = value.getFullYear();
  const month = String(value.getMonth() + 1).padStart(2, "0");
  const day = String(value.getDate()).padStart(2, "0");
  const hours = String(value.getHours()).padStart(2, "0");
  const minutes = String(value.getMinutes()).padStart(2, "0");
  return `${year}-${month}-${day}T${hours}:${minutes}`;
}

export function defaultStrategyDraft(): StrategyConfigDraft {
  return {
    symbol: "AAPL",
    assetClass: "stock",
    interval: "1d",
    warmupBars: 80,
    minConfidence: 0.1,
    persistSummary: true,
    runName: "",
    sourceState: {
      mode: "inline",
      providerName: "oanda",
      start: defaultDateTimeLocal(-60),
      end: defaultDateTimeLocal(0),
      limit: "",
      inlineBars: 220
    }
  };
}

export function defaultMlDraft(): MLConfigDraft {
  return {
    symbol: "AAPL",
    assetClass: "stock",
    interval: "1d",
    horizonBars: 5,
    taskType: "classification",
    persistSummary: true,
    runName: "",
    sourceState: {
      mode: "inline",
      providerName: "oanda",
      start: defaultDateTimeLocal(-120),
      end: defaultDateTimeLocal(0),
      limit: "",
      inlineBars: 260
    }
  };
}

function buildFetchSource(value: CandleSourceDraftState): MarketDataFetchSource {
  return {
    source_type: "market_data_fetch",
    provider_name: value.providerName.trim(),
    start: asUtcIso(value.start),
    end: asUtcIso(value.end),
    ...(value.limit.trim() ? { limit: Number(value.limit) } : {})
  };
}

export function strategyDraftToRunRequest(
  draft: StrategyConfigDraft
): StrategyRunRequest {
  const candleSource =
    draft.sourceState.mode === "inline"
      ? {
          source_type: "inline_candles" as const,
          candles: generateSampleCandles(draft.sourceState.inlineBars)
        }
      : buildFetchSource(draft.sourceState);
  return {
    instrument: {
      symbol: draft.symbol.trim().toUpperCase(),
      asset_class: draft.assetClass
    },
    interval: draft.interval,
    candle_source: candleSource,
    strategy_spec: {
      strategy_id: "technical_rule_v1",
      backtest_config: {
        warmup_bars: draft.warmupBars,
        min_signal_confidence: draft.minConfidence
      }
    },
    run_config: {
      run_name: draft.runName || undefined,
      persist_summary: draft.persistSummary,
      strict_failures: true
    }
  };
}

export function mlDraftToRunRequest(draft: MLConfigDraft): MLRunRequest {
  const candleSource =
    draft.sourceState.mode === "inline"
      ? {
          source_type: "inline_candles" as const,
          candles: generateSampleCandles(draft.sourceState.inlineBars)
        }
      : buildFetchSource(draft.sourceState);
  const returnLabel = `ret_h${draft.horizonBars}`;
  const directionLabel = `dir_h${draft.horizonBars}`;
  return {
    instrument: {
      symbol: draft.symbol.trim().toUpperCase(),
      asset_class: draft.assetClass
    },
    interval: draft.interval,
    candle_source: candleSource,
    ml_spec: {
      task_type: draft.taskType,
      label_specs:
        draft.taskType === "classification"
          ? [
              {
                label_type: "future_return",
                horizon_bars: draft.horizonBars,
                name: returnLabel
              },
              {
                label_type: "direction",
                horizon_bars: draft.horizonBars,
                name: directionLabel
              }
            ]
          : [
              {
                label_type: "future_return",
                horizon_bars: draft.horizonBars,
                name: returnLabel
              }
            ],
      target_label: draft.taskType === "classification" ? directionLabel : returnLabel,
      model_specs:
        draft.taskType === "classification"
          ? [{ model_id: "dummy_cls", family: "dummy_classifier" }]
          : [{ model_id: "dummy_reg", family: "dummy_regressor" }]
    },
    run_config: {
      run_name: draft.runName || undefined,
      persist_summary: draft.persistSummary,
      strict_failures: true
    }
  };
}

export function strategyDraftToSavedPayload(
  draft: StrategyConfigDraft
): SavedStrategyConfigPayload {
  return {
    instrument: {
      symbol: draft.symbol.trim().toUpperCase(),
      asset_class: draft.assetClass
    },
    interval: draft.interval,
    candle_source:
      draft.sourceState.mode === "inline"
        ? {
            source_type: "inline_sample",
            inline_bars: draft.sourceState.inlineBars
          }
        : buildFetchSource(draft.sourceState),
    strategy_spec: {
      strategy_id: "technical_rule_v1",
      backtest_config: {
        warmup_bars: draft.warmupBars,
        min_signal_confidence: draft.minConfidence
      }
    },
    run_config: {
      run_name: draft.runName || undefined,
      persist_summary: draft.persistSummary,
      strict_failures: true
    }
  };
}

export function mlDraftToSavedPayload(draft: MLConfigDraft): SavedMLConfigPayload {
  const returnLabel = `ret_h${draft.horizonBars}`;
  const directionLabel = `dir_h${draft.horizonBars}`;
  return {
    instrument: {
      symbol: draft.symbol.trim().toUpperCase(),
      asset_class: draft.assetClass
    },
    interval: draft.interval,
    candle_source:
      draft.sourceState.mode === "inline"
        ? {
            source_type: "inline_sample",
            inline_bars: draft.sourceState.inlineBars
          }
        : buildFetchSource(draft.sourceState),
    ml_spec: {
      task_type: draft.taskType,
      label_specs:
        draft.taskType === "classification"
          ? [
              {
                label_type: "future_return",
                horizon_bars: draft.horizonBars,
                name: returnLabel
              },
              {
                label_type: "direction",
                horizon_bars: draft.horizonBars,
                name: directionLabel
              }
            ]
          : [
              {
                label_type: "future_return",
                horizon_bars: draft.horizonBars,
                name: returnLabel
              }
            ],
      target_label: draft.taskType === "classification" ? directionLabel : returnLabel,
      model_specs:
        draft.taskType === "classification"
          ? [{ model_id: "dummy_cls", family: "dummy_classifier" }]
          : [{ model_id: "dummy_reg", family: "dummy_regressor" }]
    },
    run_config: {
      run_name: draft.runName || undefined,
      persist_summary: draft.persistSummary,
      strict_failures: true
    }
  };
}

export function strategyDraftFromSavedPayload(
  payload: SavedStrategyConfigPayload
): StrategyConfigDraft {
  const base = defaultStrategyDraft();
  return {
    ...base,
    symbol: payload.instrument.symbol,
    assetClass: payload.instrument.asset_class,
    interval: payload.interval,
    warmupBars: payload.strategy_spec?.backtest_config?.warmup_bars ?? base.warmupBars,
    minConfidence:
      payload.strategy_spec?.backtest_config?.min_signal_confidence ?? base.minConfidence,
    persistSummary: payload.run_config?.persist_summary ?? base.persistSummary,
    runName: payload.run_config?.run_name ?? "",
    sourceState:
      payload.candle_source.source_type === "inline_sample"
        ? {
            ...base.sourceState,
            mode: "inline",
            inlineBars: payload.candle_source.inline_bars
          }
        : {
            mode: "fetch",
            providerName: payload.candle_source.provider_name,
            start: asDateTimeLocal(payload.candle_source.start),
            end: asDateTimeLocal(payload.candle_source.end),
            limit:
              payload.candle_source.limit === undefined
                ? ""
                : String(payload.candle_source.limit),
            inlineBars: base.sourceState.inlineBars
          }
  };
}

export function mlDraftFromSavedPayload(payload: SavedMLConfigPayload): MLConfigDraft {
  const base = defaultMlDraft();
  const targetLabel = payload.ml_spec?.target_label ?? "";
  return {
    ...base,
    symbol: payload.instrument.symbol,
    assetClass: payload.instrument.asset_class,
    interval: payload.interval,
    horizonBars:
      payload.ml_spec?.label_specs?.[0]?.horizon_bars ?? base.horizonBars,
    taskType: targetLabel.startsWith("dir_") ? "classification" : "regression",
    persistSummary: payload.run_config?.persist_summary ?? base.persistSummary,
    runName: payload.run_config?.run_name ?? "",
    sourceState:
      payload.candle_source.source_type === "inline_sample"
        ? {
            ...base.sourceState,
            mode: "inline",
            inlineBars: payload.candle_source.inline_bars
          }
        : {
            mode: "fetch",
            providerName: payload.candle_source.provider_name,
            start: asDateTimeLocal(payload.candle_source.start),
            end: asDateTimeLocal(payload.candle_source.end),
            limit:
              payload.candle_source.limit === undefined
                ? ""
                : String(payload.candle_source.limit),
            inlineBars: base.sourceState.inlineBars
          }
  };
}
