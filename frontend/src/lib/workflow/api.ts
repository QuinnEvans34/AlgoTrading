import { requestJson } from "../api/client";
import type {
  DeleteWorkflowObjectResponse,
  RecentAsset,
  RecentAssetListResponse,
  RecentAssetTouchRequest,
  RecentCompareSet,
  RecentCompareSetListResponse,
  RecentCompareTouchRequest,
  SavedConfigType,
  SavedResearchConfig,
  SavedResearchConfigCreateRequest,
  SavedResearchConfigListResponse,
  SavedResearchConfigUpdateRequest,
  WatchlistItem,
  WatchlistItemWriteRequest,
  WatchlistResponse
} from "./types";

function asQuery(params: Record<string, string | number | undefined | null>): string {
  const query = new URLSearchParams();
  Object.entries(params).forEach(([key, value]) => {
    if (value !== undefined && value !== null && `${value}`.trim() !== "") {
      query.set(key, String(value));
    }
  });
  const rendered = query.toString();
  return rendered.length > 0 ? `?${rendered}` : "";
}

export function listSavedConfigs(
  configType?: SavedConfigType,
  limit = 100
): Promise<SavedResearchConfigListResponse> {
  return requestJson<SavedResearchConfigListResponse>(
    `/workflow/saved-configs${asQuery({ config_type: configType, limit })}`
  );
}

export function createSavedConfig(
  payload: SavedResearchConfigCreateRequest
): Promise<SavedResearchConfig> {
  return requestJson<SavedResearchConfig>("/workflow/saved-configs", {
    method: "POST",
    body: JSON.stringify(payload)
  });
}

export function fetchSavedConfig(configId: string): Promise<SavedResearchConfig> {
  return requestJson<SavedResearchConfig>(
    `/workflow/saved-configs/${encodeURIComponent(configId)}`
  );
}

export function updateSavedConfig(
  configId: string,
  payload: SavedResearchConfigUpdateRequest
): Promise<SavedResearchConfig> {
  return requestJson<SavedResearchConfig>(
    `/workflow/saved-configs/${encodeURIComponent(configId)}`,
    {
      method: "PUT",
      body: JSON.stringify(payload)
    }
  );
}

export function deleteSavedConfig(
  configId: string
): Promise<DeleteWorkflowObjectResponse> {
  return requestJson<DeleteWorkflowObjectResponse>(
    `/workflow/saved-configs/${encodeURIComponent(configId)}`,
    { method: "DELETE" }
  );
}

export function fetchWatchlist(limit = 100): Promise<WatchlistResponse> {
  return requestJson<WatchlistResponse>(`/workflow/watchlist${asQuery({ limit })}`);
}

export function addWatchlistItem(
  payload: WatchlistItemWriteRequest
): Promise<WatchlistItem> {
  return requestJson<WatchlistItem>("/workflow/watchlist/items", {
    method: "POST",
    body: JSON.stringify(payload)
  });
}

export function deleteWatchlistItem(
  assetClass: string,
  symbol: string
): Promise<DeleteWorkflowObjectResponse> {
  return requestJson<DeleteWorkflowObjectResponse>(
    `/workflow/watchlist/items/${encodeURIComponent(assetClass)}/${encodeURIComponent(symbol)}`,
    { method: "DELETE" }
  );
}

export function fetchRecentAssets(limit = 20): Promise<RecentAssetListResponse> {
  return requestJson<RecentAssetListResponse>(
    `/workflow/recent-assets${asQuery({ limit })}`
  );
}

export function touchRecentAsset(
  payload: RecentAssetTouchRequest
): Promise<RecentAsset> {
  return requestJson<RecentAsset>("/workflow/recent-assets/touch", {
    method: "POST",
    body: JSON.stringify(payload)
  });
}

export function fetchRecentCompares(limit = 20): Promise<RecentCompareSetListResponse> {
  return requestJson<RecentCompareSetListResponse>(
    `/workflow/recent-compares${asQuery({ limit })}`
  );
}

export function touchRecentCompare(
  payload: RecentCompareTouchRequest
): Promise<RecentCompareSet> {
  return requestJson<RecentCompareSet>("/workflow/recent-compares/touch", {
    method: "POST",
    body: JSON.stringify(payload)
  });
}
