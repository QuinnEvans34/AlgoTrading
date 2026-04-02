import type { AssetClass, BarInterval } from "../api/types";
import type { CompareMode } from "../history/types";
import type { MLConfigDraft, StrategyConfigDraft } from "../workflow/drafts";

const INTERVALS: BarInterval[] = ["1m", "5m", "15m", "30m", "1h", "4h", "1d"];

export interface AssetIdentity {
  symbol: string;
  assetClass: AssetClass;
}

export interface AssetQueryPrefill {
  symbol?: string;
  assetClass?: AssetClass;
  interval?: BarInterval;
  configId?: string;
}

export function isAssetClass(value: string | null | undefined): value is AssetClass {
  return value === "stock" || value === "forex";
}

export function isBarInterval(value: string | null | undefined): value is BarInterval {
  return value !== undefined && value !== null && INTERVALS.includes(value as BarInterval);
}

export function normalizeAssetSymbol(symbol: string): string {
  return symbol.trim().toUpperCase();
}

export function buildAssetDetailPath(assetClass: AssetClass, symbol: string): string {
  return `/assets/${encodeURIComponent(assetClass)}/${encodeURIComponent(
    normalizeAssetSymbol(symbol)
  )}`;
}

export function buildResearchLabPath(
  basePath: "/strategy" | "/ml",
  asset: AssetIdentity,
  interval?: BarInterval,
  configId?: string
): string {
  const params = new URLSearchParams({
    symbol: normalizeAssetSymbol(asset.symbol),
    assetClass: asset.assetClass
  });
  if (interval) {
    params.set("interval", interval);
  }
  if (configId) {
    params.set("configId", configId);
  }
  return `${basePath}?${params.toString()}`;
}

export function buildHistoryPath(symbol: string): string {
  return `/history?q=${encodeURIComponent(normalizeAssetSymbol(symbol))}`;
}

export function buildComparePath(runIds: string[], mode: CompareMode): string {
  const params = new URLSearchParams({
    ids: runIds.join(","),
    mode
  });
  return `/compare?${params.toString()}`;
}

export function parseAssetQueryPrefill(
  searchParams: URLSearchParams
): AssetQueryPrefill {
  const symbol = searchParams.get("symbol");
  const assetClass = searchParams.get("assetClass");
  const interval = searchParams.get("interval");
  const configId = searchParams.get("configId");
  return {
    symbol: symbol ? normalizeAssetSymbol(symbol) : undefined,
    assetClass: isAssetClass(assetClass) ? assetClass : undefined,
    interval: isBarInterval(interval) ? interval : undefined,
    configId: configId?.trim() ? configId : undefined
  };
}

export function applyStrategyQueryPrefill(
  draft: StrategyConfigDraft,
  prefill: AssetQueryPrefill
): StrategyConfigDraft {
  return {
    ...draft,
    symbol: prefill.symbol ?? draft.symbol,
    assetClass: prefill.assetClass ?? draft.assetClass,
    interval: prefill.interval ?? draft.interval
  };
}

export function applyMlQueryPrefill(
  draft: MLConfigDraft,
  prefill: AssetQueryPrefill
): MLConfigDraft {
  return {
    ...draft,
    symbol: prefill.symbol ?? draft.symbol,
    assetClass: prefill.assetClass ?? draft.assetClass,
    interval: prefill.interval ?? draft.interval
  };
}
