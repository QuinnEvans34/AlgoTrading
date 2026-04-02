import { useEffect, useMemo, useState } from "react";
import { Link } from "react-router-dom";

import { ErrorAlert } from "../components/common/ErrorAlert";
import { LoadingState } from "../components/common/LoadingState";
import { useAssetWorkspace } from "../hooks/useAssetWorkspace";
import { fetchHealth } from "../lib/api/health";
import { fetchCapabilities } from "../lib/api/metadata";
import type { AssetClass, CapabilitiesResponse, HealthResponse } from "../lib/api/types";
import {
  buildFallbackCatalogAsset,
  FEATURED_FOREX,
  FEATURED_STOCKS,
  findCatalogAsset,
  type CatalogAsset
} from "../lib/catalog/assets";
import { fetchRunHistory } from "../lib/history/api";
import type { RunHistoryItem } from "../lib/history/types";
import {
  buildAssetDetailPath,
  buildComparePath,
  buildResearchLabPath,
  isAssetClass
} from "../lib/research/navigation";
import { fetchRecentCompares, listSavedConfigs } from "../lib/workflow/api";
import type {
  RecentCompareSet,
  SavedResearchConfigSummary
} from "../lib/workflow/types";

function resolveCatalogAsset(symbol: string, assetClass: string): CatalogAsset {
  const resolvedAssetClass: AssetClass = isAssetClass(assetClass) ? assetClass : "stock";
  return (
    findCatalogAsset(resolvedAssetClass, symbol) ??
    buildFallbackCatalogAsset(resolvedAssetClass, symbol)
  );
}

function runPrimaryLink(run: RunHistoryItem): string {
  if (run.has_strategy) {
    return `/runs/${encodeURIComponent(run.run_id)}/strategy`;
  }
  return `/runs/${encodeURIComponent(run.run_id)}/ml`;
}

export function DashboardPage() {
  const assetWorkspace = useAssetWorkspace();
  const [health, setHealth] = useState<HealthResponse | null>(null);
  const [capabilities, setCapabilities] = useState<CapabilitiesResponse | null>(null);
  const [strategyConfigs, setStrategyConfigs] = useState<SavedResearchConfigSummary[]>([]);
  const [mlConfigs, setMlConfigs] = useState<SavedResearchConfigSummary[]>([]);
  const [recentCompares, setRecentCompares] = useState<RecentCompareSet[]>([]);
  const [recentRuns, setRecentRuns] = useState<RunHistoryItem[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<unknown>(null);

  useEffect(() => {
    async function loadDashboard() {
      setLoading(true);
      setError(null);
      try {
        const [
          healthResponse,
          capabilitiesResponse,
          strategyConfigsResponse,
          mlConfigsResponse,
          recentCompareResponse,
          recentRunsResponse
        ] = await Promise.all([
          fetchHealth(),
          fetchCapabilities(),
          listSavedConfigs("strategy", 4),
          listSavedConfigs("ml", 4),
          fetchRecentCompares(5),
          fetchRunHistory({ limit: 6, offset: 0, sort: "started_desc" })
        ]);
        setHealth(healthResponse);
        setCapabilities(capabilitiesResponse);
        setStrategyConfigs(strategyConfigsResponse.items);
        setMlConfigs(mlConfigsResponse.items);
        setRecentCompares(recentCompareResponse.items);
        setRecentRuns(recentRunsResponse.items);
      } catch (err) {
        setError(err);
      } finally {
        setLoading(false);
      }
    }

    void loadDashboard();
  }, []);

  const watchlistAssets = useMemo(
    () =>
      assetWorkspace.watchlist
        .slice(0, 5)
        .map((item) => resolveCatalogAsset(item.symbol, item.asset_class)),
    [assetWorkspace.watchlist]
  );

  const recentAssetCards = useMemo(
    () =>
      assetWorkspace.recentAssets
        .slice(0, 5)
        .map((item) => resolveCatalogAsset(item.symbol, item.asset_class)),
    [assetWorkspace.recentAssets]
  );

  return (
    <section className="page">
      <section className="dashboard-hero">
        <div>
          <p className="eyebrow">Research Platform</p>
          <h2>Dashboard</h2>
          <p>
            Start with curated markets, continue through your watchlist and recent
            assets, and hand off directly into Strategy Lab, ML Lab, History, or
            Compare when the research path is clear.
          </p>
        </div>
        <div className="dashboard-quick-links card-grid">
          <Link className="dashboard-link-card" to="/stocks">
            <strong>Explore Stocks</strong>
            <span>Browse curated equity names and jump into asset detail.</span>
          </Link>
          <Link className="dashboard-link-card" to="/forex">
            <strong>Explore Forex</strong>
            <span>Focus on major pairs and macro-aware research entry points.</span>
          </Link>
          <Link className="dashboard-link-card" to="/strategy">
            <strong>Open Strategy Lab</strong>
            <span>Launch a saved or ad hoc strategy workflow.</span>
          </Link>
          <Link className="dashboard-link-card" to="/ml">
            <strong>Open ML Lab</strong>
            <span>Build feature, label, and model experiments.</span>
          </Link>
        </div>
      </section>

      {loading || assetWorkspace.loading ? (
        <LoadingState label="Loading dashboard..." />
      ) : null}
      {error ? <ErrorAlert error={error} /> : null}
      {assetWorkspace.error ? <ErrorAlert error={assetWorkspace.error} /> : null}

      <section className="dashboard-grid">
        <section className="result-panel">
          <h2>Watchlist</h2>
          <p>Your persisted watchlist now anchors the research entry point.</p>
          {watchlistAssets.length === 0 ? (
            <>
              <p>No watchlist assets yet.</p>
              <div className="asset-chip-row">
                {FEATURED_STOCKS.slice(0, 2).map((asset) => (
                  <Link key={asset.symbol} to={buildAssetDetailPath(asset.assetClass, asset.symbol)}>
                    {asset.symbol}
                  </Link>
                ))}
                {FEATURED_FOREX.slice(0, 2).map((asset) => (
                  <Link key={asset.symbol} to={buildAssetDetailPath(asset.assetClass, asset.symbol)}>
                    {asset.symbol}
                  </Link>
                ))}
              </div>
            </>
          ) : (
            <div className="asset-card-grid">
              {watchlistAssets.map((asset) => (
                <article key={`${asset.assetClass}:${asset.symbol}`} className="asset-card">
                  <div className="asset-card-header">
                    <div>
                      <p className="eyebrow">{asset.assetClass}</p>
                      <h3>{asset.symbol}</h3>
                    </div>
                    <button
                      type="button"
                      disabled={assetWorkspace.busy}
                      onClick={() =>
                        void assetWorkspace.toggleWatchlist(
                          { symbol: asset.symbol, assetClass: asset.assetClass },
                          "dashboard_watchlist"
                        )
                      }
                    >
                      Remove
                    </button>
                  </div>
                  <p>{asset.name}</p>
                  <p>{asset.headline}</p>
                  <div className="asset-chip-row">
                    {asset.tags.slice(0, 3).map((tag) => (
                      <span key={tag} className="asset-chip">
                        {tag}
                      </span>
                    ))}
                  </div>
                  <div className="controls-row">
                    <Link
                      to={buildAssetDetailPath(asset.assetClass, asset.symbol)}
                      onClick={() =>
                        void assetWorkspace.markRecent(
                          { symbol: asset.symbol, assetClass: asset.assetClass },
                          "dashboard_detail"
                        )
                      }
                    >
                      Open Detail
                    </Link>
                    <Link
                      to={buildResearchLabPath(
                        "/strategy",
                        { symbol: asset.symbol, assetClass: asset.assetClass },
                        asset.preferredInterval
                      )}
                    >
                      Strategy Lab
                    </Link>
                  </div>
                </article>
              ))}
            </div>
          )}
        </section>

        <section className="result-panel">
          <h2>Recent Assets</h2>
          <p>Continue the symbols and pairs you touched most recently.</p>
          {recentAssetCards.length === 0 ? (
            <p>No recent assets yet.</p>
          ) : (
            <ul className="simple-list">
              {recentAssetCards.map((asset) => (
                <li key={`${asset.assetClass}:${asset.symbol}`}>
                  <Link to={buildAssetDetailPath(asset.assetClass, asset.symbol)}>
                    {asset.symbol}
                  </Link>{" "}
                  <span>{asset.name}</span>
                </li>
              ))}
            </ul>
          )}
        </section>

        <section className="result-panel">
          <h2>Saved Config Snapshot</h2>
          <div className="nested-panel">
            <h3>Strategy Templates</h3>
            {strategyConfigs.length === 0 ? (
              <p>No saved strategy configs yet.</p>
            ) : (
              <ul className="simple-list">
                {strategyConfigs.map((config) => (
                  <li key={config.id}>
                    <Link
                      to={buildResearchLabPath(
                        "/strategy",
                        {
                          symbol: config.instrument_symbol,
                          assetClass: isAssetClass(config.asset_class)
                            ? config.asset_class
                            : "stock"
                        },
                        undefined,
                        config.id
                      )}
                    >
                      {config.name}
                    </Link>{" "}
                    <span>{config.instrument_symbol}</span>
                  </li>
                ))}
              </ul>
            )}
          </div>
          <div className="nested-panel">
            <h3>ML Templates</h3>
            {mlConfigs.length === 0 ? (
              <p>No saved ML configs yet.</p>
            ) : (
              <ul className="simple-list">
                {mlConfigs.map((config) => (
                  <li key={config.id}>
                    <Link
                      to={buildResearchLabPath(
                        "/ml",
                        {
                          symbol: config.instrument_symbol,
                          assetClass: isAssetClass(config.asset_class)
                            ? config.asset_class
                            : "stock"
                        },
                        undefined,
                        config.id
                      )}
                    >
                      {config.name}
                    </Link>{" "}
                    <span>{config.instrument_symbol}</span>
                  </li>
                ))}
              </ul>
            )}
          </div>
        </section>

        <section className="result-panel">
          <h2>Recent Runs</h2>
          {recentRuns.length === 0 ? (
            <p>No saved runs discovered yet.</p>
          ) : (
            <ul className="simple-list">
              {recentRuns.map((run) => (
                <li key={run.run_id}>
                  <Link to={runPrimaryLink(run)}>{run.run_name}</Link>{" "}
                  <span>
                    {run.instrument_symbol} · {run.workflow_type}
                  </span>
                </li>
              ))}
            </ul>
          )}
          <div className="controls-row">
            <Link to="/history">Open Full History</Link>
          </div>
        </section>

        <section className="result-panel">
          <h2>Recent Compares</h2>
          {recentCompares.length === 0 ? (
            <p>No recent compare selections yet.</p>
          ) : (
            <ul className="simple-list">
              {recentCompares.map((item) => (
                <li key={item.id}>
                  <Link to={buildComparePath(item.run_ids, item.compare_mode)}>
                    {item.compare_mode}
                  </Link>{" "}
                  <span>{item.run_ids.join(", ")}</span>
                </li>
              ))}
            </ul>
          )}
        </section>

        <section className="result-panel">
          <h2>System Status</h2>
          <div className="summary-grid">
            <div className="info-item">
              <span>Health</span>
              <strong>{health?.status ?? "unknown"}</strong>
            </div>
            <div className="info-item">
              <span>Providers</span>
              <strong>{capabilities?.providers.length ?? 0}</strong>
            </div>
            <div className="info-item">
              <span>Research API</span>
              <strong>
                {capabilities?.feature_flags?.research_api_enabled ? "enabled" : "disabled"}
              </strong>
            </div>
            <div className="info-item">
              <span>Compare API</span>
              <strong>
                {capabilities?.feature_flags?.compare_api_enabled ? "enabled" : "disabled"}
              </strong>
            </div>
          </div>
        </section>
      </section>
    </section>
  );
}
