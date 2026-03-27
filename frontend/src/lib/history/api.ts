import { requestJson } from "../api/client";
import type {
  CompareRunsRequest,
  CompareRunsResponse,
  HistoryReadResponse,
  RunHistoryListResponse
} from "./types";

export interface HistoryListQuery {
  workflow_type?: string;
  status?: string;
  q?: string;
  started_after?: string;
  started_before?: string;
  limit?: number;
  offset?: number;
  sort?: "started_desc" | "started_asc";
}

function toQueryString(query: HistoryListQuery): string {
  const params = new URLSearchParams();
  Object.entries(query).forEach(([key, value]) => {
    if (value !== undefined && value !== null && `${value}`.trim() !== "") {
      params.set(key, String(value));
    }
  });
  const rendered = params.toString();
  return rendered ? `?${rendered}` : "";
}

export function fetchRunHistory(query: HistoryListQuery): Promise<RunHistoryListResponse> {
  return requestJson<RunHistoryListResponse>(`/history/runs${toQueryString(query)}`);
}

export function fetchHistoryRun(runId: string): Promise<HistoryReadResponse> {
  return requestJson<HistoryReadResponse>(`/history/runs/${encodeURIComponent(runId)}`);
}

export function compareRuns(payload: CompareRunsRequest): Promise<CompareRunsResponse> {
  return requestJson<CompareRunsResponse>("/compare/runs", {
    method: "POST",
    body: JSON.stringify(payload)
  });
}
