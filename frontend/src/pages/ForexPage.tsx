import { useMemo, useState } from "react";
import { Link } from "react-router-dom";

import { ErrorAlert } from "../components/common/ErrorAlert";
import { LoadingState } from "../components/common/LoadingState";
import { useAssetWorkspace } from "../hooks/useAssetWorkspace";
import {
  FEATURED_FOREX,
  filterCatalogAssets,
  type ForexCatalogAsset
} from "../lib/catalog/assets";
import {
  buildAssetDetailPath,
  buildResearchLabPath
} from "../lib/research/navigation";

function asForexAssets(query: string): ForexCatalogAsset[] {
  return filterCatalogAssets("forex", query) as ForexCatalogAsset[];
}

export function ForexPage() {
  const assetWorkspace = useAssetWorkspace();
  const [query, setQuery] = useState("");

  const matchingAssets = useMemo(() => asForexAssets(query), [query]);
  const featuredSymbols = new Set(FEATURED_FOREX.map((asset) => asset.symbol));
  const watchlistSymbols = new Set(
    assetWorkspace.watchlist
      .filter((item) => item.asset_class === "forex")
      .map((item) => item.symbol)
  );

  return (
    <section className="page">
      <h2>Forex Explorer</h2>
      <p>
        Focus on major pairs, keep macro context visible, and move cleanly into
        asset detail or Strategy Lab.
      </p>

      {assetWorkspace.loading ? <LoadingState label="Loading forex explorer..." /> : null}
      {assetWorkspace.error ? <ErrorAlert error={assetWorkspace.error} /> : null}

      <section className="result-panel">
        <h2>Search Major Pairs</h2>
        <label className="field-inline compact">
          <span>Search</span>
          <input
            aria-label="Search forex pairs"
            value={query}
            onChange={(event) => setQuery(event.target.value)}
            placeholder="pair, region, macro driver"
          />
        </label>
      </section>

      <section className="result-panel">
        <h2>Watchlist Pairs</h2>
        {assetWorkspace.watchlist.filter((item) => item.asset_class === "forex").length === 0 ? (
          <p>No forex watchlist entries yet.</p>
        ) : (
          <div className="asset-chip-row">
            {assetWorkspace.watchlist
              .filter((item) => item.asset_class === "forex")
              .map((item) => (
                <Link
                  key={item.id}
                  to={buildAssetDetailPath("forex", item.symbol)}
                  onClick={() =>
                    void assetWorkspace.markRecent(
                      { symbol: item.symbol, assetClass: "forex" },
                      "forex_watchlist"
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
                  <p className="eyebrow">
                    {featuredSymbols.has(asset.symbol) ? "Major Pair" : "Research Pair"}
                  </p>
                  <h3>
                    {asset.symbol} · {asset.name}
                  </h3>
                </div>
                <button
                  type="button"
                  disabled={assetWorkspace.busy}
                  onClick={() =>
                    void assetWorkspace.toggleWatchlist(
                      { symbol: asset.symbol, assetClass: "forex" },
                      "forex_explorer"
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
                  to={buildAssetDetailPath("forex", asset.symbol)}
                  onClick={() =>
                    void assetWorkspace.markRecent(
                      { symbol: asset.symbol, assetClass: "forex" },
                      "forex_detail"
                    )
                  }
                >
                  Open Detail
                </Link>
                <Link
                  to={buildResearchLabPath(
                    "/strategy",
                    { symbol: asset.symbol, assetClass: "forex" },
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
