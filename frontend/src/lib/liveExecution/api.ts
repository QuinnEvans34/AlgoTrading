import { requestJson } from "../api/client";
import type {
  LiveExecutionAttemptsResponse,
  LiveExecutionReadinessResponse,
  LiveExecutionStatusResponse,
  LiveIntentValidationResponse,
  ManualLiveOrderRequest,
  ManualLiveSubmitResponse,
  LiveSubmitResponse,
  LiveTradeIntentRequest
} from "./types";

export function fetchLiveExecutionStatus(): Promise<LiveExecutionStatusResponse> {
  return requestJson<LiveExecutionStatusResponse>("/live-execution/status");
}

export function fetchLiveExecutionReadiness(): Promise<LiveExecutionReadinessResponse> {
  return requestJson<LiveExecutionReadinessResponse>("/live-execution/readiness");
}

export function validateLiveTradeIntent(
  payload: LiveTradeIntentRequest
): Promise<LiveIntentValidationResponse> {
  return requestJson<LiveIntentValidationResponse>("/live-execution/intents/validate", {
    method: "POST",
    body: JSON.stringify(payload)
  });
}

export function submitLiveTradeIntent(
  payload: LiveTradeIntentRequest
): Promise<LiveSubmitResponse> {
  return requestJson<LiveSubmitResponse>("/live-execution/intents/submit", {
    method: "POST",
    body: JSON.stringify(payload)
  });
}

export function submitManualLiveOrder(
  payload: ManualLiveOrderRequest
): Promise<ManualLiveSubmitResponse> {
  return requestJson<ManualLiveSubmitResponse>("/live-execution/manual-orders", {
    method: "POST",
    body: JSON.stringify(payload)
  });
}

export function fetchLiveExecutionAttempts(
  limit = 25
): Promise<LiveExecutionAttemptsResponse> {
  return requestJson<LiveExecutionAttemptsResponse>(
    `/live-execution/attempts?limit=${encodeURIComponent(String(limit))}`
  );
}
