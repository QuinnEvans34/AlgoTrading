import { requestJson } from "./client";
import type {
  MarketDataPreviewRequest,
  MarketDataPreviewResponse
} from "./types";

export function fetchHistoricalPreview(
  payload: MarketDataPreviewRequest
): Promise<MarketDataPreviewResponse> {
  return requestJson<MarketDataPreviewResponse>("/market-data/historical-preview", {
    method: "POST",
    body: JSON.stringify(payload)
  });
}
