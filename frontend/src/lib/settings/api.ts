import { requestJson } from "../api/client";
import type { SystemSettingsResponse } from "./types";

export function fetchSystemSettings(): Promise<SystemSettingsResponse> {
  return requestJson<SystemSettingsResponse>("/settings/system");
}

