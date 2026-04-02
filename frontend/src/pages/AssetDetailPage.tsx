import { type FormEvent, useEffect, useMemo, useState } from "react";
import { Link, useParams, useSearchParams } from "react-router-dom";

import { ErrorAlert } from "../components/common/ErrorAlert";
import { LoadingState } from "../components/common/LoadingState";
import { PricePreviewChart } from "../components/research/PricePreviewChart";
import { useAssetWorkspace } from "../hooks/useAssetWorkspace";
import {
  askAssetResearchQuestion,
  generateAssetResearchMemo
} from "../lib/api/assetResearch";
import { fetchHistoricalPreview } from "../lib/api/marketData";
import { fetchCapabilities } from "../lib/api/metadata";
import type {
  AskAssetResearchQuestionResponse,
  AssetClass,
  CapabilitiesResponse,
  Candle,
  GenerateAssetMemoResponse,
  MarketDataPreviewResponse
} from "../lib/api/types";
import {
  buildFallbackCatalogAsset,
  findCatalogAsset,
  type CatalogAsset
} from "../lib/catalog/assets";
import { fetchRunHistory } from "../lib/history/api";
import type { RunHistoryItem } from "../lib/history/types";
import {
  buildComparePath,
  buildHistoryPath,
  buildResearchLabPath,
  isAssetClass,
  normalizeAssetSymbol
} from "../lib/research/navigation";
import { listSavedConfigs } from "../lib/workflow/api";
import type { SavedResearchConfigSummary } from "../lib/workflow/types";

type AssetTab = "profile" | "filings" | "macro" | "performance" | "ai";

function coerceTab(assetClass: AssetClass, value: string | null): AssetTab {
  const allowed =
    assetClass === "stock"
      ? ["profile", "filings", "performance", "ai"]
      : ["profile", "macro", "performance", "ai"];
  return (value && allowed.includes(value) ? value : "profile") as AssetTab;
}

function resolveAsset(assetClass: AssetClass, symbol: string): CatalogAsset {
  return (
    findCatalogAsset(assetClass, symbol) ??
    buildFallbackCatalogAsset(assetClass, symbol)
  );
}

function previewRange(days: number): { start: string; end: string } {
  const end = new Date();
  const start = new Date(end);
  start.setDate(start.getDate() - days);
  return { start: start.toISOString(), end: end.toISOString() };
}

function metricSummary(candles: Candle[]) {
  if (candles.length === 0) {
    return null;
  }
  const first = candles[0].close;
  const last = candles[candles.length - 1].close;
  const high = Math.max(...candles.map((candle) => candle.high));
  const low = Math.min(...candles.map((candle) => candle.low));
  return {
    last,
    change: last - first,
    changePct: first === 0 ? 0 : ((last - first) / first) * 100,
    high,
    low,
    candles: candles.length
  };
}

export function AssetDetailPage() {
  const params = useParams();
  const [searchParams, setSearchParams] = useSearchParams();
  const assetWorkspace = useAssetWorkspace();

  const assetClass = isAssetClass(params.assetClass) ? params.assetClass : "stock";
  const symbol = normalizeAssetSymbol(params.symbol ?? "AAPL");
  const asset = useMemo(() => resolveAsset(assetClass, symbol), [assetClass, symbol]);
  const tab = coerceTab(assetClass, searchParams.get("tab"));

  const [capabilities, setCapabilities] = useState<CapabilitiesResponse | null>(null);
  const [strategyConfigs, setStrategyConfigs] = useState<SavedResearchConfigSummary[]>([]);
  const [mlConfigs, setMlConfigs] = useState<SavedResearchConfigSummary[]>([]);
  const [relatedRuns, setRelatedRuns] = useState<RunHistoryItem[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<unknown>(null);

  const [preview, setPreview] = useState<MarketDataPreviewResponse | null>(null);
  const [previewLoading, setPreviewLoading] = useState(false);
  const [previewError, setPreviewError] = useState<unknown>(null);
  const [previewUnavailable, setPreviewUnavailable] = useState<string | null>(null);
  const [memo, setMemo] = useState<GenerateAssetMemoResponse | null>(null);
  const [memoLoading, setMemoLoading] = useState(false);
  const [memoError, setMemoError] = useState<unknown>(null);
  const [questionInput, setQuestionInput] = useState("");
  const [questionResponse, setQuestionResponse] =
    useState<AskAssetResearchQuestionResponse | null>(null);
  const [questionLoading, setQuestionLoading] = useState(false);
  const [questionError, setQuestionError] = useState<unknown>(null);

  useEffect(() => {
    async function loadContext() {
      setLoading(true);
      setError(null);
      try {
        const [capabilitiesResponse, strategyResponse, mlResponse, historyResponse] =
          await Promise.all([
            fetchCapabilities(),
            listSavedConfigs("strategy", 100),
            listSavedConfigs("ml", 100),
            fetchRunHistory({
              q: symbol,
              limit: 12,
              offset: 0,
              sort: "started_desc"
            })
          ]);
        setCapabilities(capabilitiesResponse);
        setStrategyConfigs(strategyResponse.items);
        setMlConfigs(mlResponse.items);
        setRelatedRuns(
          historyResponse.items.filter(
            (run) =>
              normalizeAssetSymbol(run.instrument_symbol) === symbol &&
              (run.asset_class === undefined ||
                run.asset_class === null ||
                run.asset_class === assetClass)
          )
        );
      } catch (err) {
        setError(err);
      } finally {
        setLoading(false);
      }
    }

    void loadContext();
  }, [assetClass, symbol]);

  useEffect(() => {
    void assetWorkspace.markRecent({ symbol, assetClass }, "asset_detail");
  }, [assetClass, assetWorkspace, symbol]);

  useEffect(() => {
    setPreview(null);
    setPreviewError(null);
    setPreviewUnavailable(null);
    setMemo(null);
    setMemoError(null);
    setMemoLoading(false);
    setQuestionResponse(null);
    setQuestionInput("");
    setQuestionError(null);
    setQuestionLoading(false);
  }, [assetClass, symbol]);

  useEffect(() => {
    async function loadPreview() {
      if (tab !== "performance" || !capabilities) {
        return;
      }
      const providerName = capabilities.providers[0];
      if (!providerName) {
        setPreviewUnavailable("No market-data provider is currently available for preview.");
        return;
      }
      const { start, end } = previewRange(asset.performanceLookbackDays);
      setPreviewLoading(true);
      setPreviewError(null);
      setPreviewUnavailable(null);
      try {
        const response = await fetchHistoricalPreview({
          provider_name: providerName,
          instrument: {
            symbol,
            asset_class: assetClass
          },
          interval: asset.preferredInterval,
          start,
          end
        });
        setPreview(response);
      } catch (err) {
        setPreview(null);
        setPreviewError(err);
        setPreviewUnavailable(
          "Historical preview is not currently available for this asset via the configured provider path."
        );
      } finally {
        setPreviewLoading(false);
      }
    }

    if (
      preview === null &&
      previewLoading === false &&
      previewError === null &&
      previewUnavailable === null
    ) {
      void loadPreview();
    }
  }, [
    asset.performanceLookbackDays,
    asset.preferredInterval,
    assetClass,
    capabilities,
    previewError,
    previewUnavailable,
    preview,
    previewLoading,
    symbol,
    tab
  ]);

  const matchingStrategyConfigs = useMemo(
    () =>
      strategyConfigs.filter(
        (config) =>
          normalizeAssetSymbol(config.instrument_symbol) === symbol &&
          (config.asset_class === assetClass || !isAssetClass(config.asset_class))
      ),
    [assetClass, strategyConfigs, symbol]
  );

  const matchingMlConfigs = useMemo(
    () =>
      mlConfigs.filter(
        (config) =>
          normalizeAssetSymbol(config.instrument_symbol) === symbol &&
          (config.asset_class === assetClass || !isAssetClass(config.asset_class))
      ),
    [assetClass, mlConfigs, symbol]
  );

  const strategyRuns = relatedRuns.filter((run) => run.has_strategy);
  const mlRuns = relatedRuns.filter((run) => run.has_ml);
  const summary = preview ? metricSummary(preview.candles) : null;

  async function handleGenerateMemo() {
    setMemoLoading(true);
    setMemoError(null);
    try {
      const response = await generateAssetResearchMemo({
        asset_class: asset.assetClass,
        symbol: asset.symbol
      });
      setMemo(response);
    } catch (err) {
      setMemoError(err);
    } finally {
      setMemoLoading(false);
    }
  }

  async function handleSubmitQuestion(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    if (questionInput.trim().length < 3) {
      return;
    }
    setQuestionLoading(true);
    setQuestionError(null);
    try {
      const response = await askAssetResearchQuestion({
        asset_class: asset.assetClass,
        symbol: asset.symbol,
        question: questionInput.trim()
      });
      setQuestionResponse(response);
    } catch (err) {
      setQuestionError(err);
    } finally {
      setQuestionLoading(false);
    }
  }

  return (
    <section className="page">
      <div className="controls-row">
        <Link to={assetClass === "stock" ? "/stocks" : "/forex"}>
          Back to {assetClass === "stock" ? "Stocks" : "Forex"}
        </Link>
      </div>

      <section className="asset-detail-hero result-panel">
        <div className="asset-card-header">
          <div>
            <p className="eyebrow">{asset.assetClass === "stock" ? "Asset Detail" : "FX Detail"}</p>
            <h2>
              {asset.symbol} · {asset.name}
            </h2>
            <p>{asset.headline}</p>
          </div>
          <button
            type="button"
            disabled={assetWorkspace.busy}
            onClick={() =>
              void assetWorkspace.toggleWatchlist(
                { symbol: asset.symbol, assetClass: asset.assetClass },
                "asset_detail_toggle"
              )
            }
          >
            {assetWorkspace.isInWatchlist(asset.symbol, asset.assetClass)
              ? "Remove from Watchlist"
              : "Add to Watchlist"}
          </button>
        </div>

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
            to={buildResearchLabPath(
              "/strategy",
              { symbol: asset.symbol, assetClass: asset.assetClass },
              asset.preferredInterval
            )}
          >
            Open Strategy Lab
          </Link>
          <Link
            to={buildResearchLabPath(
              "/ml",
              { symbol: asset.symbol, assetClass: asset.assetClass },
              asset.preferredInterval
            )}
          >
            Open ML Lab
          </Link>
          <Link to={buildHistoryPath(asset.symbol)}>View Related Runs</Link>
        </div>
      </section>

      {loading || assetWorkspace.loading ? (
        <LoadingState label="Loading asset research context..." />
      ) : null}
      {error ? <ErrorAlert error={error} /> : null}
      {assetWorkspace.error ? <ErrorAlert error={assetWorkspace.error} /> : null}

      <section className="result-panel">
        <div className="tab-row" role="tablist" aria-label="Asset detail sections">
          {(assetClass === "stock"
            ? [
                { key: "profile", label: "Profile" },
                { key: "filings", label: "Filings" },
                { key: "performance", label: "Performance" },
                { key: "ai", label: "AI" }
              ]
            : [
                { key: "profile", label: "Profile" },
                { key: "macro", label: "Macro" },
                { key: "performance", label: "Performance" },
                { key: "ai", label: "AI" }
              ]
          ).map((item) => (
            <button
              key={item.key}
              type="button"
              role="tab"
              aria-selected={tab === item.key}
              className={tab === item.key ? "tab-button active" : "tab-button"}
              onClick={() => setSearchParams({ tab: item.key }, { replace: true })}
            >
              {item.label}
            </button>
          ))}
        </div>
      </section>

      {tab === "profile" ? (
        <>
          <section className="result-panel">
            <h2>Profile</h2>
            <div className="summary-grid">
              <div className="info-item">
                <span>Symbol</span>
                <strong>{asset.symbol}</strong>
              </div>
              <div className="info-item">
                <span>Asset Class</span>
                <strong>{asset.assetClass}</strong>
              </div>
              <div className="info-item">
                <span>{asset.assetClass === "stock" ? "Sector" : "Region"}</span>
                <strong>{asset.assetClass === "stock" ? asset.sector : asset.region}</strong>
              </div>
              <div className="info-item">
                <span>Preferred Interval</span>
                <strong>{asset.preferredInterval}</strong>
              </div>
            </div>
          </section>
          <section className="result-panel">
            <h2>Research Notes</h2>
            <ul className="simple-list">
              {asset.profileBullets.map((item) => (
                <li key={item}>{item}</li>
              ))}
            </ul>
          </section>
        </>
      ) : null}

      {tab === "filings" && asset.assetClass === "stock" ? (
        <>
          <section className="result-panel">
            <h2>Filings Focus</h2>
            <p>
              This tab is intentionally structured around research priorities rather
              than a fabricated filing feed.
            </p>
            <ul className="simple-list">
              {asset.filingsFocus.map((item) => (
                <li key={item}>{item}</li>
              ))}
            </ul>
          </section>
          <section className="result-panel">
            <h2>Performance Checklist</h2>
            <ul className="simple-list">
              {asset.performanceFocus.map((item) => (
                <li key={item}>{item}</li>
              ))}
            </ul>
          </section>
        </>
      ) : null}

      {tab === "macro" && asset.assetClass === "forex" ? (
        <>
          <section className="result-panel">
            <h2>Macro Drivers</h2>
            <ul className="simple-list">
              {asset.macroDrivers.map((item) => (
                <li key={item}>{item}</li>
              ))}
            </ul>
          </section>
          <section className="result-panel">
            <h2>Performance Checklist</h2>
            <ul className="simple-list">
              {asset.performanceFocus.map((item) => (
                <li key={item}>{item}</li>
              ))}
            </ul>
          </section>
        </>
      ) : null}

      {tab === "performance" ? (
        <>
          {previewLoading ? <LoadingState label="Loading performance preview..." /> : null}
          {previewUnavailable ? (
            <section className="result-panel">
              <h2>Performance</h2>
              <p>{previewUnavailable}</p>
            </section>
          ) : null}
          {previewError ? <ErrorAlert error={previewError} /> : null}
          {summary ? (
            <section className="result-panel">
              <h2>Performance Snapshot</h2>
              <div className="summary-grid">
                <div className="info-item">
                  <span>Latest Close</span>
                  <strong>{summary.last.toFixed(4)}</strong>
                </div>
                <div className="info-item">
                  <span>Net Change</span>
                  <strong>
                    {summary.change.toFixed(4)} ({summary.changePct.toFixed(2)}%)
                  </strong>
                </div>
                <div className="info-item">
                  <span>Range</span>
                  <strong>
                    {summary.low.toFixed(4)} - {summary.high.toFixed(4)}
                  </strong>
                </div>
                <div className="info-item">
                  <span>Candle Count</span>
                  <strong>{summary.candles}</strong>
                </div>
              </div>
            </section>
          ) : null}
          {preview ? (
            <PricePreviewChart
              title={`${asset.symbol} Performance Preview`}
              candles={preview.candles}
            />
          ) : null}
        </>
      ) : null}

      {tab === "ai" ? (
        <>
          <section className="result-panel">
            <div className="asset-card-header">
              <div>
                <h2>Grounded AI Research</h2>
                <p>
                  Generate a structured memo or ask a single grounded research
                  question using the asset catalog, saved configs, related runs,
                  and any compatible market preview data available on the backend.
                </p>
              </div>
              <button
                type="button"
                onClick={() => void handleGenerateMemo()}
                disabled={memoLoading || questionLoading}
              >
                {memoLoading ? "Generating Memo..." : "Generate Research Memo"}
              </button>
            </div>

            {memoError ? <ErrorAlert error={memoError} /> : null}
            {memoLoading ? <LoadingState label="Generating grounded research memo..." /> : null}
            {memo ? (
              <div className="nested-panel">
                <p className="eyebrow">Memo</p>
                {memo.sections.map((section) => (
                  <div key={section.title} className="nested-panel">
                    <h3>{section.title}</h3>
                    <p>{section.content}</p>
                  </div>
                ))}
                {memo.grounding.length > 0 ? (
                  <div className="nested-panel">
                    <h3>Grounding</h3>
                    <ul className="simple-list">
                      {memo.grounding.map((item) => (
                        <li key={`${item.source}-${item.status}-${item.detail}`}>
                          <strong>{item.source}</strong>: {item.detail}
                        </li>
                      ))}
                    </ul>
                  </div>
                ) : null}
                {memo.warnings.length > 0 ? (
                  <div className="nested-panel">
                    <h3>Warnings</h3>
                    <ul className="simple-list">
                      {memo.warnings.map((item) => (
                        <li key={item}>{item}</li>
                      ))}
                    </ul>
                  </div>
                ) : null}
              </div>
            ) : (
              <p>
                No memo has been generated yet. Use the button above to create a
                structured research memo for this asset.
              </p>
            )}
          </section>

          <section className="result-panel">
            <h2>Prompt-Driven Question</h2>
            <div className="asset-chip-row">
              {asset.aiPrompts.map((item) => (
                <button
                  key={item}
                  type="button"
                  className="asset-chip"
                  onClick={() => setQuestionInput(item)}
                >
                  {item}
                </button>
              ))}
            </div>
            <form onSubmit={(event) => void handleSubmitQuestion(event)}>
              <label className="field-label" htmlFor="asset-research-question">
                Grounded research question
              </label>
              <textarea
                id="asset-research-question"
                value={questionInput}
                onChange={(event) => setQuestionInput(event.target.value)}
                rows={4}
                placeholder="Ask a grounded question about this asset."
              />
              <div className="controls-row">
                <button
                  type="submit"
                  disabled={questionLoading || questionInput.trim().length < 3}
                >
                  {questionLoading ? "Answering..." : "Ask Question"}
                </button>
              </div>
            </form>
            {questionError ? <ErrorAlert error={questionError} /> : null}
            {questionResponse ? (
              <div className="nested-panel">
                <h3>Answer</h3>
                <p>{questionResponse.answer}</p>
                {questionResponse.grounding.length > 0 ? (
                  <div className="nested-panel">
                    <h3>Grounding</h3>
                    <ul className="simple-list">
                      {questionResponse.grounding.map((item) => (
                        <li key={`${item.source}-${item.status}-${item.detail}`}>
                          <strong>{item.source}</strong>: {item.detail}
                        </li>
                      ))}
                    </ul>
                  </div>
                ) : null}
                {questionResponse.warnings.length > 0 ? (
                  <div className="nested-panel">
                    <h3>Warnings</h3>
                    <ul className="simple-list">
                      {questionResponse.warnings.map((item) => (
                        <li key={item}>{item}</li>
                      ))}
                    </ul>
                  </div>
                ) : null}
              </div>
            ) : (
              <p>Ask a single grounded question to inspect this asset more closely.</p>
            )}
          </section>

          <section className="result-panel">
            <h2>Saved Configs</h2>
            <div className="nested-panel">
              <h3>Strategy Templates</h3>
              {matchingStrategyConfigs.length === 0 ? (
                <p>No saved strategy configs are pinned to this asset yet.</p>
              ) : (
                <ul className="simple-list">
                  {matchingStrategyConfigs.map((config) => (
                    <li key={config.id}>
                      <Link
                        to={buildResearchLabPath(
                          "/strategy",
                          { symbol: asset.symbol, assetClass: asset.assetClass },
                          asset.preferredInterval,
                          config.id
                        )}
                      >
                        {config.name}
                      </Link>
                    </li>
                  ))}
                </ul>
              )}
            </div>
            <div className="nested-panel">
              <h3>ML Templates</h3>
              {matchingMlConfigs.length === 0 ? (
                <p>No saved ML configs are pinned to this asset yet.</p>
              ) : (
                <ul className="simple-list">
                  {matchingMlConfigs.map((config) => (
                    <li key={config.id}>
                      <Link
                        to={buildResearchLabPath(
                          "/ml",
                          { symbol: asset.symbol, assetClass: asset.assetClass },
                          asset.preferredInterval,
                          config.id
                        )}
                      >
                        {config.name}
                      </Link>
                    </li>
                  ))}
                </ul>
              )}
            </div>
          </section>

          <section className="result-panel">
            <h2>Related Runs</h2>
            {relatedRuns.length === 0 ? (
              <p>No saved runs were found for this asset yet.</p>
            ) : (
              <ul className="simple-list">
                {relatedRuns.map((run) => (
                  <li key={run.run_id}>
                    <Link
                      to={
                        run.has_strategy
                          ? `/runs/${encodeURIComponent(run.run_id)}/strategy`
                          : `/runs/${encodeURIComponent(run.run_id)}/ml`
                      }
                    >
                      {run.run_name}
                    </Link>{" "}
                    <span>
                      {run.workflow_type} · {run.status}
                    </span>
                  </li>
                ))}
              </ul>
            )}
          </section>

          <section className="result-panel">
            <h2>Compare-Ready Paths</h2>
            <ul className="simple-list">
              {strategyRuns.length >= 2 ? (
                <li>
                  <Link
                    to={buildComparePath(
                      strategyRuns.slice(0, 2).map((run) => run.run_id),
                      "strategy"
                    )}
                  >
                    Compare the latest strategy runs
                  </Link>
                </li>
              ) : null}
              {mlRuns.length >= 2 ? (
                <li>
                  <Link
                    to={buildComparePath(
                      mlRuns.slice(0, 2).map((run) => run.run_id),
                      "ml"
                    )}
                  >
                    Compare the latest ML runs
                  </Link>
                </li>
              ) : null}
              {strategyRuns.length < 2 && mlRuns.length < 2 ? (
                <li>Create at least two compatible saved runs to unlock compare from this page.</li>
              ) : null}
            </ul>
          </section>

          <section className="result-panel">
            <h2>AI Research Prompt Suggestions</h2>
            <ul className="simple-list">
              {asset.aiPrompts.map((item) => (
                <li key={item}>{item}</li>
              ))}
            </ul>
          </section>
        </>
      ) : null}
    </section>
  );
}
