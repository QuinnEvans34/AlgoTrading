import { requestJson } from "./client";
import type { HealthResponse } from "./types";

export function fetchHealth(): Promise<HealthResponse> {
  return requestJson<HealthResponse>("/health");
}

