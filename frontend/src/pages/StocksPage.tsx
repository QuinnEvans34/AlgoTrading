import { useMemo, useState } from "react";
import { Link } from "react-router-dom";

import { ErrorAlert } from "../components/common/ErrorAlert";
import { LoadingState } from "../components/common/LoadingState";
import { useAssetWorkspace } from "../hooks/useAssetWorkspace";
import {
  filterCatalogAssets,
  groupStocksBySector,
  type StockCatalogAsset
} from "../lib/catalog/assets";
import {
  buildAssetDetailPath,
  buildResearchLabPath
} from "../lib/research/navigation";

function asStockAssets(query: string): StockCatalogAsset[] {
  return filterCatalogAssets("stock", query) as StockCatalogAsset[];
}

export function StocksPage() {
  const assetWorkspace = useAssetWorkspace();
  const [query, setQuery] = useState("");
  const [sectorFilter, setSectorFilter] = useState("all");

  const matchingAssets = useMemo(
    () =>
      asStockAssets(query).filter((asset) =>
        sectorFilter === "all" ? true : asset.sector === sectorFilter
      ),
    [query, sectorFilter]
  );

  const watchlistSymbols = new Set(
    assetWorkspace.watchlist
      .filter((item) => item.asset_class === "stock")
      .map((item) => item.symbol)
  );

  const sectors = useMemo(
    () => ["all", ...new Set(groupStocksBySector().map((group) => group.label))],
    []
  );

  return (
    <section className="page">
      <h2>Stocks Explorer</h2>
      <p>
        Browse a curated set of research-ready equities, keep watchlist state
        visible, and move directly into asset detail or Strategy Lab.
      </p>

      {assetWorkspace.loading ? <LoadingState label="Loading stock explorer..." /> : null}
      {assetWorkspace.error ? <ErrorAlert error={assetWorkspace.error} /> : null}

      <section className="result-panel">
        <h2>Search and Browse</h2>
        <div className="filters-grid">
          <label className="field-inline compact">
            <span>Search</span>
            <input
              aria-label="Search stocks"
              value={query}
              onChange={(event) => setQuery(event.target.value)}
              placeholder="symbol, company, sector, theme"
            />
          </label>
          <label className="field-inline compact">
            <span>Sector</span>
            <select
              aria-label="Stock sector"
              value={sectorFilter}
              onChange={(event) => setSectorFilter(event.target.value)}
            >
              {sectors.map((sector) => (
                <option key={sector} value={sector}>
                  {sector}
                </option>
              ))}
            </select>
          </label>
        </div>
      </section>

      <section className="result-panel">
        <h2>Your Stock Watchlist</h2>
        {assetWorkspace.watchlist.filter((item) => item.asset_class === "stock").length === 0 ? (
          <p>No stock watchlist entries yet.</p>
        ) : (
          <div className="asset-chip-row">
            {assetWorkspace.watchlist
              .filter((item) => item.asset_class === "stock")
              .map((item) => (
                <Link
                  key={item.id}
                  to={buildAssetDetailPath("stock", item.symbol)}
                  onClick={() =>
                    void assetWorkspace.markRecent(
                      { symbol: item.symbol, assetClass: "stock" },
                      "stocks_watchlist"
                    )
                  }
                >
                  {item.symbol}
                </Link>
              ))}
          </div>
        )}
      </section>

      <section className="asset-card-grid">
        {matchingAssets.map((asset) => {
          const inWatchlist = watchlistSymbols.has(asset.symbol);
          return (
            <article key={asset.symbol} className="asset-card">
              <div className="asset-card-header">
                <div>
                  <p className="eyebrow">{asset.sector}</p>
                  <h3>
                    {asset.symbol} · {asset.name}
                  </h3>
                </div>
                <button
                  type="button"
                  disabled={assetWorkspace.busy}
                  onClick={() =>
                    void assetWorkspace.toggleWatchlist(
                      { symbol: asset.symbol, assetClass: "stock" },
                      "stocks_explorer"
                    )
                  }
                >
                  {inWatchlist ? "Remove" : "Watchlist"}
                </button>
              </div>
              <p>{asset.headline}</p>
              <p>{asset.description}</p>
              <div className="asset-chip-row">
                {asset.tags.map((tag) => (
                  <span key={tag} className="asset-chip">
                    {tag}
                  </span>
                ))}
              </div>
              <div className="controls-row">
                <Link
                  to={buildAssetDetailPath("stock", asset.symbol)}
                  onClick={() =>
                    void assetWorkspace.markRecent(
                      { symbol: asset.symbol, assetClass: "stock" },
                      "stocks_detail"
                    )
                  }
                >
                  Open Detail
                </Link>
                <Link
                  to={buildResearchLabPath(
                    "/strategy",
                    { symbol: asset.symbol, assetClass: "stock" },
                    asset.preferredInterval
                  )}
                >
                  Strategy Lab
                </Link>
              </div>
            </article>
          );
        })}
      </section>
    </section>
  );
}
