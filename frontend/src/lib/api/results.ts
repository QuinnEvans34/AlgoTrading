import { requestJson } from "./client";
import type {
  RunDetailResponse,
  RunSummaryResponse,
  StoredRunSummaryListResponse
} from "./types";

export function fetchStoredRuns(limit = 50): Promise<StoredRunSummaryListResponse> {
  return requestJson<StoredRunSummaryListResponse>(
    `/research/runs?limit=${encodeURIComponent(String(limit))}`
  );
}

export function fetchStoredRunSummary(runId: string): Promise<RunSummaryResponse> {
  return requestJson<RunSummaryResponse>(
    `/research/runs/${encodeURIComponent(runId)}/summary`
  );
}

export function fetchStoredRunDetail(runId: string): Promise<RunDetailResponse> {
  return requestJson<RunDetailResponse>(
    `/research/runs/${encodeURIComponent(runId)}/detail`
  );
}
