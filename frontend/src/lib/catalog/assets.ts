import type { AssetClass, BarInterval } from "../api/types";
import catalogData from "./assetCatalog.json";

export interface CatalogAssetBase {
  symbol: string;
  assetClass: AssetClass;
  name: string;
  headline: string;
  description: string;
  tags: string[];
  preferredInterval: BarInterval;
  performanceLookbackDays: number;
  profileBullets: string[];
  performanceFocus: string[];
  aiPrompts: string[];
}

export interface StockCatalogAsset extends CatalogAssetBase {
  assetClass: "stock";
  sector: string;
  exchange: string;
  filingsFocus: string[];
}

export interface ForexCatalogAsset extends CatalogAssetBase {
  assetClass: "forex";
  region: string;
  macroDrivers: string[];
}

export type CatalogAsset = StockCatalogAsset | ForexCatalogAsset;

interface CatalogData {
  stocks: StockCatalogAsset[];
  forex: ForexCatalogAsset[];
}

const typedCatalog = catalogData as CatalogData;

export const STOCK_CATALOG: StockCatalogAsset[] = typedCatalog.stocks;
export const FOREX_CATALOG: ForexCatalogAsset[] = typedCatalog.forex;

const ALL_ASSETS: CatalogAsset[] = [...STOCK_CATALOG, ...FOREX_CATALOG];

export function normalizeCatalogSymbol(symbol: string): string {
  return symbol.trim().toUpperCase();
}

export function findCatalogAsset(
  assetClass: AssetClass,
  symbol: string
): CatalogAsset | null {
  const normalized = normalizeCatalogSymbol(symbol);
  return (
    ALL_ASSETS.find(
      (asset) => asset.assetClass === assetClass && asset.symbol === normalized
    ) ?? null
  );
}

export function buildFallbackCatalogAsset(
  assetClass: AssetClass,
  symbol: string
): CatalogAsset {
  const normalized = normalizeCatalogSymbol(symbol);
  if (assetClass === "forex") {
    return {
      symbol: normalized,
      assetClass,
      name: normalized.replace("_", " / "),
      headline: "Uncatalogued FX pair opened directly from the product.",
      description:
        "This asset is not yet part of the curated explorer catalog, but you can still launch research and use watchlist continuity.",
      tags: ["custom", "research"],
      preferredInterval: "4h",
      performanceLookbackDays: 120,
      region: "Custom FX",
      profileBullets: [
        "Treat this page as a research launch surface rather than a full market profile.",
        "Use history and compare to inspect prior work on this pair."
      ],
      macroDrivers: [
        "Relative policy path",
        "Macro surprise flow",
        "Risk sentiment"
      ],
      performanceFocus: [
        "Trend persistence on the chosen interval",
        "Range behavior in quiet sessions",
        "Response to macro catalysts"
      ],
      aiPrompts: [
        "Launch ML research using the existing saved-config workflow.",
        "Compare runs after you have at least two compatible saved results."
      ]
    };
  }
  return {
    symbol: normalized,
    assetClass,
    name: normalized,
    headline: "Uncatalogued equity opened directly from the product.",
    description:
      "This asset is not yet part of the curated stock explorer, but it still supports watchlist, history, and research handoff.",
    tags: ["custom", "research"],
    preferredInterval: "1d",
    performanceLookbackDays: 180,
    sector: "Custom Equity",
    exchange: "Custom",
    profileBullets: [
      "Use this page to route into Strategy Lab, ML Lab, and related run history.",
      "Add the asset to your watchlist if it should become part of your regular workflow."
    ],
    filingsFocus: [
      "Quarterly revenue and margin trend",
      "Management guidance changes",
      "Risk factors that affect the current thesis"
    ],
    performanceFocus: [
      "Reaction to earnings and guidance",
      "Trend quality on the chosen interval",
      "Relative strength versus your watchlist"
    ],
    aiPrompts: [
      "Save a strategy template if you revisit this symbol frequently.",
      "Use compare once multiple runs exist for the same name."
    ]
  };
}

export function filterCatalogAssets(
  assetClass: AssetClass,
  query: string
): CatalogAsset[] {
  const normalized = query.trim().toUpperCase();
  const source = assetClass === "stock" ? STOCK_CATALOG : FOREX_CATALOG;
  if (!normalized) {
    return source;
  }
  return source.filter((asset) => {
    const haystack = [
      asset.symbol,
      asset.name,
      asset.headline,
      asset.description,
      ...asset.tags,
      ...(asset.assetClass === "stock"
        ? [asset.sector, asset.exchange]
        : [asset.region, ...asset.macroDrivers])
    ]
      .join(" ")
      .toUpperCase();
    return haystack.includes(normalized);
  });
}

export function groupStocksBySector(): Array<{
  label: string;
  items: StockCatalogAsset[];
}> {
  const groups = new Map<string, StockCatalogAsset[]>();
  STOCK_CATALOG.forEach((asset) => {
    groups.set(asset.sector, [...(groups.get(asset.sector) ?? []), asset]);
  });
  return Array.from(groups.entries()).map(([label, items]) => ({ label, items }));
}

export const FEATURED_STOCKS = STOCK_CATALOG.slice(0, 4);
export const FEATURED_FOREX = FOREX_CATALOG.slice(0, 4);
