import { useEffect, useState } from "react";
import { Link, useSearchParams } from "react-router-dom";

import { ErrorAlert } from "../components/common/ErrorAlert";
import { LoadingState } from "../components/common/LoadingState";
import { MLRunForm } from "../components/forms/MLRunForm";
import { RunSummaryPanel } from "../components/results/RunSummaryPanel";
import { StepResultsTable } from "../components/results/StepResultsTable";
import { AssetWorkflowPanel } from "../components/workflow/AssetWorkflowPanel";
import { ConfigLibraryPanel } from "../components/workflow/ConfigLibraryPanel";
import { fetchCapabilities } from "../lib/api/metadata";
import { createMlRun } from "../lib/api/research";
import type { MLRunRequest, RunSummaryResponse } from "../lib/api/types";
import {
  applyMlQueryPrefill,
  parseAssetQueryPrefill
} from "../lib/research/navigation";
import {
  addWatchlistItem,
  createSavedConfig,
  deleteSavedConfig,
  deleteWatchlistItem,
  fetchRecentAssets,
  fetchSavedConfig,
  fetchWatchlist,
  listSavedConfigs,
  touchRecentAsset,
  updateSavedConfig
} from "../lib/workflow/api";
import {
  defaultMlDraft,
  mlDraftFromSavedPayload,
  mlDraftToSavedPayload,
  type MLConfigDraft
} from "../lib/workflow/drafts";
import type {
  RecentAsset,
  SavedResearchConfigSummary,
  WatchlistItem
} from "../lib/workflow/types";

export function MLRunPage() {
  const [searchParams] = useSearchParams();
  const [providers, setProviders] = useState<string[]>([]);
  const [draft, setDraft] = useState<MLConfigDraft>(defaultMlDraft());
  const [result, setResult] = useState<RunSummaryResponse | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<unknown>(null);

  const [workflowLoading, setWorkflowLoading] = useState(true);
  const [workflowBusy, setWorkflowBusy] = useState(false);
  const [workflowError, setWorkflowError] = useState<unknown>(null);
  const [savedConfigs, setSavedConfigs] = useState<SavedResearchConfigSummary[]>([]);
  const [watchlist, setWatchlist] = useState<WatchlistItem[]>([]);
  const [recentAssets, setRecentAssets] = useState<RecentAsset[]>([]);
  const [loadedConfigId, setLoadedConfigId] = useState<string | null>(null);
  const [saveName, setSaveName] = useState("");
  const [saveDescription, setSaveDescription] = useState("");

  async function refreshWorkflowPanels() {
    const [configsResponse, watchlistResponse, recentAssetsResponse] = await Promise.all([
      listSavedConfigs("ml"),
      fetchWatchlist(),
      fetchRecentAssets()
    ]);
    setSavedConfigs(configsResponse.items);
    setWatchlist(watchlistResponse.items);
    setRecentAssets(recentAssetsResponse.items);
  }

  useEffect(() => {
    async function loadPage() {
      setWorkflowLoading(true);
      try {
        const [capabilities] = await Promise.all([fetchCapabilities(), refreshWorkflowPanels()]);
        setProviders(capabilities.providers);
      } catch (err) {
        setWorkflowError(err);
        try {
          const capabilities = await fetchCapabilities();
          setProviders(capabilities.providers);
        } catch {
          setProviders([]);
        }
      } finally {
        setWorkflowLoading(false);
      }
    }
    void loadPage();
  }, []);

  useEffect(() => {
    const prefill = parseAssetQueryPrefill(searchParams);
    if (prefill.configId) {
      void loadSavedConfig(prefill.configId);
      return;
    }
    if (prefill.symbol || prefill.assetClass || prefill.interval) {
      setDraft((current) => applyMlQueryPrefill(current, prefill));
    }
  }, [searchParams]);

  async function submit(payload: MLRunRequest) {
    setLoading(true);
    setError(null);
    setResult(null);
    try {
      const response = await createMlRun(payload);
      setResult(response);
      try {
        await touchRecentAsset({
          symbol: draft.symbol.trim().toUpperCase(),
          asset_class: draft.assetClass,
          source_context: "ml_submit"
        });
        const recentAssetsResponse = await fetchRecentAssets();
        setRecentAssets(recentAssetsResponse.items);
      } catch {
        // Keep workflow persistence failures from changing research-run behavior.
      }
    } catch (err) {
      setError(err);
    } finally {
      setLoading(false);
    }
  }

  async function loadSavedConfig(configId: string) {
    setWorkflowBusy(true);
    setWorkflowError(null);
    try {
      const config = await fetchSavedConfig(configId);
      setDraft(mlDraftFromSavedPayload(config.payload));
      setLoadedConfigId(config.id);
      setSaveName(config.name);
      setSaveDescription(config.description ?? "");
      const configsResponse = await listSavedConfigs("ml");
      setSavedConfigs(configsResponse.items);
    } catch (err) {
      setWorkflowError(err);
    } finally {
      setWorkflowBusy(false);
    }
  }

  async function saveNewConfig() {
    if (!saveName.trim()) {
      setWorkflowError(new Error("Saved config name is required."));
      return;
    }
    setWorkflowBusy(true);
    setWorkflowError(null);
    try {
      const created = await createSavedConfig({
        config_type: "ml",
        name: saveName.trim(),
        description: saveDescription.trim() || null,
        payload: mlDraftToSavedPayload(draft)
      });
      setLoadedConfigId(created.id);
      setSaveName(created.name);
      setSaveDescription(created.description ?? "");
      await refreshWorkflowPanels();
    } catch (err) {
      setWorkflowError(err);
    } finally {
      setWorkflowBusy(false);
    }
  }

  async function updateCurrentConfig() {
    if (!loadedConfigId) {
      return;
    }
    if (!saveName.trim()) {
      setWorkflowError(new Error("Saved config name is required."));
      return;
    }
    setWorkflowBusy(true);
    setWorkflowError(null);
    try {
      const updated = await updateSavedConfig(loadedConfigId, {
        config_type: "ml",
        name: saveName.trim(),
        description: saveDescription.trim() || null,
        payload: mlDraftToSavedPayload(draft)
      });
      setSaveName(updated.name);
      setSaveDescription(updated.description ?? "");
      await refreshWorkflowPanels();
    } catch (err) {
      setWorkflowError(err);
    } finally {
      setWorkflowBusy(false);
    }
  }

  async function removeSavedConfig(configId: string) {
    setWorkflowBusy(true);
    setWorkflowError(null);
    try {
      await deleteSavedConfig(configId);
      if (loadedConfigId === configId) {
        setLoadedConfigId(null);
      }
      await refreshWorkflowPanels();
    } catch (err) {
      setWorkflowError(err);
    } finally {
      setWorkflowBusy(false);
    }
  }

  async function addCurrentAssetToWatchlist() {
    setWorkflowBusy(true);
    setWorkflowError(null);
    try {
      await addWatchlistItem({
        symbol: draft.symbol.trim().toUpperCase(),
        asset_class: draft.assetClass,
        source_context: "ml_page"
      });
      const watchlistResponse = await fetchWatchlist();
      setWatchlist(watchlistResponse.items);
    } catch (err) {
      setWorkflowError(err);
    } finally {
      setWorkflowBusy(false);
    }
  }

  async function removeCurrentAssetFromWatchlist() {
    await removeWatchlistAsset(draft.symbol.trim().toUpperCase(), draft.assetClass);
  }

  async function removeWatchlistAsset(symbol: string, assetClass: string) {
    setWorkflowBusy(true);
    setWorkflowError(null);
    try {
      await deleteWatchlistItem(assetClass, symbol);
      const watchlistResponse = await fetchWatchlist();
      setWatchlist(watchlistResponse.items);
    } catch (err) {
      setWorkflowError(err);
    } finally {
      setWorkflowBusy(false);
    }
  }

  function applyAsset(symbol: string, assetClass: string) {
    setDraft({
      ...draft,
      symbol,
      assetClass: assetClass as MLConfigDraft["assetClass"]
    });
  }

  return (
    <section className="page">
      <h2>ML Research Run</h2>
      <p>Submit ML dataset + model run payloads to the backend orchestration API.</p>

      {workflowLoading ? <LoadingState label="Loading workflow tools..." /> : null}
      {workflowError ? <ErrorAlert error={workflowError} /> : null}

      <ConfigLibraryPanel
        title="ML Config Library"
        configs={savedConfigs}
        activeConfigId={loadedConfigId}
        saveName={saveName}
        saveDescription={saveDescription}
        busy={workflowBusy}
        onSaveNameChange={setSaveName}
        onSaveDescriptionChange={setSaveDescription}
        onSaveNew={saveNewConfig}
        onUpdateCurrent={updateCurrentConfig}
        onLoad={loadSavedConfig}
        onDelete={removeSavedConfig}
      />

      <AssetWorkflowPanel
        title="Research Watchlist"
        currentSymbol={draft.symbol}
        currentAssetClass={draft.assetClass}
        watchlist={watchlist}
        recentAssets={recentAssets}
        busy={workflowBusy}
        onAddCurrentToWatchlist={addCurrentAssetToWatchlist}
        onRemoveCurrentFromWatchlist={removeCurrentAssetFromWatchlist}
        onUseAsset={applyAsset}
        onRemoveWatchlistItem={removeWatchlistAsset}
      />

      <MLRunForm
        providers={providers}
        draft={draft}
        onChange={setDraft}
        isSubmitting={loading}
        onSubmit={submit}
      />

      {loading ? <LoadingState label="Running ML workflow..." /> : null}
      {error ? <ErrorAlert error={error} /> : null}
      {result ? (
        <>
          <section className="result-panel">
            <h2>Next Step</h2>
            <p>
              <Link to={`/runs/${encodeURIComponent(result.run_id)}/ml`}>
                Open ML Detail Page
              </Link>
            </p>
          </section>
          <RunSummaryPanel result={result} />
          <StepResultsTable steps={result.step_results} />
        </>
      ) : null}
    </section>
  );
}
