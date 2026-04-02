import { useEffect, useMemo, useState } from "react";

import type { AssetClass } from "../lib/api/types";
import {
  addWatchlistItem,
  deleteWatchlistItem,
  fetchRecentAssets,
  fetchWatchlist,
  touchRecentAsset
} from "../lib/workflow/api";
import type { RecentAsset, WatchlistItem } from "../lib/workflow/types";
import { normalizeAssetSymbol } from "../lib/research/navigation";

export interface AssetWorkspaceTarget {
  symbol: string;
  assetClass: AssetClass;
}

function assetKey(symbol: string, assetClass: string): string {
  return `${assetClass}:${normalizeAssetSymbol(symbol)}`;
}

export function useAssetWorkspace() {
  const [watchlist, setWatchlist] = useState<WatchlistItem[]>([]);
  const [recentAssets, setRecentAssets] = useState<RecentAsset[]>([]);
  const [loading, setLoading] = useState(true);
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState<unknown>(null);

  async function refresh() {
    const [watchlistResponse, recentAssetsResponse] = await Promise.all([
      fetchWatchlist(),
      fetchRecentAssets()
    ]);
    setWatchlist(watchlistResponse.items);
    setRecentAssets(recentAssetsResponse.items);
  }

  useEffect(() => {
    async function load() {
      setLoading(true);
      setError(null);
      try {
        await refresh();
      } catch (err) {
        setError(err);
      } finally {
        setLoading(false);
      }
    }
    void load();
  }, []);

  const watchlistKeys = useMemo(
    () => new Set(watchlist.map((item) => assetKey(item.symbol, item.asset_class))),
    [watchlist]
  );

  function isInWatchlist(symbol: string, assetClass: AssetClass): boolean {
    return watchlistKeys.has(assetKey(symbol, assetClass));
  }

  async function toggleWatchlist(
    target: AssetWorkspaceTarget,
    sourceContext: string
  ) {
    const symbol = normalizeAssetSymbol(target.symbol);
    setBusy(true);
    setError(null);
    try {
      if (isInWatchlist(symbol, target.assetClass)) {
        await deleteWatchlistItem(target.assetClass, symbol);
      } else {
        await addWatchlistItem({
          symbol,
          asset_class: target.assetClass,
          source_context: sourceContext
        });
      }
      const watchlistResponse = await fetchWatchlist();
      setWatchlist(watchlistResponse.items);
    } catch (err) {
      setError(err);
    } finally {
      setBusy(false);
    }
  }

  async function markRecent(target: AssetWorkspaceTarget, sourceContext: string) {
    setError(null);
    try {
      await touchRecentAsset({
        symbol: normalizeAssetSymbol(target.symbol),
        asset_class: target.assetClass,
        source_context: sourceContext
      });
      const recentAssetsResponse = await fetchRecentAssets();
      setRecentAssets(recentAssetsResponse.items);
    } catch (err) {
      setError(err);
    }
  }

  return {
    watchlist,
    recentAssets,
    loading,
    busy,
    error,
    refresh,
    isInWatchlist,
    toggleWatchlist,
    markRecent
  };
}
