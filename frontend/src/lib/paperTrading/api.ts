import { requestJson } from "../api/client";
import type {
  PaperCancelActionResponse,
  PaperOrderActionResponse,
  PaperOrderRequest,
  PaperPriceUpdateResponse,
  PaperResetRequest,
  PaperSignalIntentRequest,
  PaperStateResponse,
  PriceUpdateRequest
} from "./types";

export function fetchPaperState(fillsLimit = 100): Promise<PaperStateResponse> {
  return requestJson<PaperStateResponse>(`/paper/state?fills_limit=${encodeURIComponent(String(fillsLimit))}`);
}

export function placePaperOrder(
  payload: PaperOrderRequest
): Promise<PaperOrderActionResponse> {
  return requestJson<PaperOrderActionResponse>("/paper/orders", {
    method: "POST",
    body: JSON.stringify(payload)
  });
}

export function cancelPaperOrder(
  orderId: string
): Promise<PaperCancelActionResponse> {
  return requestJson<PaperCancelActionResponse>(
    `/paper/orders/${encodeURIComponent(orderId)}/cancel`,
    {
      method: "POST"
    }
  );
}

export function processPaperPriceUpdate(
  payload: PriceUpdateRequest
): Promise<PaperPriceUpdateResponse> {
  return requestJson<PaperPriceUpdateResponse>("/paper/prices", {
    method: "POST",
    body: JSON.stringify(payload)
  });
}

export function submitPaperSignalIntent(
  payload: PaperSignalIntentRequest
): Promise<PaperOrderActionResponse> {
  return requestJson<PaperOrderActionResponse>("/paper/signals", {
    method: "POST",
    body: JSON.stringify(payload)
  });
}

export function resetPaperAccount(
  payload: PaperResetRequest
): Promise<PaperStateResponse> {
  return requestJson<PaperStateResponse>("/paper/reset", {
    method: "POST",
    body: JSON.stringify(payload)
  });
}

