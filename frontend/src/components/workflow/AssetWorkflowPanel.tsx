import type { RecentAsset, WatchlistItem } from "../../lib/workflow/types";

interface AssetWorkflowPanelProps {
  title: string;
  currentSymbol: string;
  currentAssetClass: string;
  watchlist: WatchlistItem[];
  recentAssets: RecentAsset[];
  busy: boolean;
  onAddCurrentToWatchlist: () => Promise<void>;
  onRemoveCurrentFromWatchlist: () => Promise<void>;
  onUseAsset: (symbol: string, assetClass: string) => void;
  onRemoveWatchlistItem: (symbol: string, assetClass: string) => Promise<void>;
}

export function AssetWorkflowPanel({
  title,
  currentSymbol,
  currentAssetClass,
  watchlist,
  recentAssets,
  busy,
  onAddCurrentToWatchlist,
  onRemoveCurrentFromWatchlist,
  onUseAsset,
  onRemoveWatchlistItem
}: AssetWorkflowPanelProps) {
  const currentKey = `${currentAssetClass}:${currentSymbol.trim().toUpperCase()}`;
  const inWatchlist = watchlist.some(
    (item) => `${item.asset_class}:${item.symbol}` === currentKey
  );

  return (
    <section className="result-panel">
      <h2>{title}</h2>
      <div className="controls-row">
        <button
          type="button"
          disabled={busy || !currentSymbol.trim()}
          onClick={() =>
            void (inWatchlist ? onRemoveCurrentFromWatchlist() : onAddCurrentToWatchlist())
          }
        >
          {inWatchlist ? "Remove Current Asset" : "Add Current Asset"}
        </button>
        <span>
          Current asset: {currentSymbol.trim().toUpperCase() || "n/a"} ({currentAssetClass})
        </span>
      </div>

      <div className="nested-panel">
        <h3>Watchlist</h3>
        {watchlist.length === 0 ? (
          <p>No watchlist items yet.</p>
        ) : (
          <ul className="simple-list">
            {watchlist.map((item) => (
              <li key={item.id}>
                <strong>{item.symbol}</strong> ({item.asset_class})
                <div className="controls-row">
                  <button
                    type="button"
                    disabled={busy}
                    onClick={() => onUseAsset(item.symbol, item.asset_class)}
                  >
                    Use
                  </button>
                  <button
                    type="button"
                    disabled={busy}
                    onClick={() => void onRemoveWatchlistItem(item.symbol, item.asset_class)}
                  >
                    Remove
                  </button>
                </div>
              </li>
            ))}
          </ul>
        )}
      </div>

      <div className="nested-panel">
        <h3>Recent Assets</h3>
        {recentAssets.length === 0 ? (
          <p>No recent assets yet.</p>
        ) : (
          <ul className="simple-list">
            {recentAssets.map((item) => (
              <li key={item.id}>
                <strong>{item.symbol}</strong> ({item.asset_class})
                <div className="controls-row">
                  <button
                    type="button"
                    disabled={busy}
                    onClick={() => onUseAsset(item.symbol, item.asset_class)}
                  >
                    Use
                  </button>
                </div>
              </li>
            ))}
          </ul>
        )}
      </div>
    </section>
  );
}
