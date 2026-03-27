import { requestJson } from "./client";
import type { CapabilitiesResponse } from "./types";

export function fetchCapabilities(): Promise<CapabilitiesResponse> {
  return requestJson<CapabilitiesResponse>("/metadata/capabilities");
}

