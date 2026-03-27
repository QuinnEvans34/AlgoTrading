import { requestJson } from "./client";
import type {
  HybridRunRequest,
  MLRunRequest,
  RunSummaryResponse,
  StrategyRunRequest
} from "./types";

export function createStrategyRun(
  payload: StrategyRunRequest
): Promise<RunSummaryResponse> {
  return requestJson<RunSummaryResponse>("/research/strategy-runs", {
    method: "POST",
    body: JSON.stringify(payload)
  });
}

export function createMlRun(
  payload: MLRunRequest
): Promise<RunSummaryResponse> {
  return requestJson<RunSummaryResponse>("/research/ml-runs", {
    method: "POST",
    body: JSON.stringify(payload)
  });
}

export function createHybridRun(
  payload: HybridRunRequest
): Promise<RunSummaryResponse> {
  return requestJson<RunSummaryResponse>("/research/hybrid-runs", {
    method: "POST",
    body: JSON.stringify(payload)
  });
}

