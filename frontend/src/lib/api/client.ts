import { API_BASE_URL } from "../config";
import type { ApiErrorEnvelope } from "./types";

export class ApiClientError extends Error {
  status: number;
  code?: string;
  details?: Record<string, unknown> | null;

  constructor(
    message: string,
    status: number,
    code?: string,
    details?: Record<string, unknown> | null
  ) {
    super(message);
    this.name = "ApiClientError";
    this.status = status;
    this.code = code;
    this.details = details;
  }
}

function isApiErrorEnvelope(value: unknown): value is ApiErrorEnvelope {
  if (typeof value !== "object" || value === null) {
    return false;
  }
  const maybeEnvelope = value as { error?: unknown };
  if (typeof maybeEnvelope.error !== "object" || maybeEnvelope.error === null) {
    return false;
  }
  const maybeError = maybeEnvelope.error as { code?: unknown; message?: unknown };
  return typeof maybeError.code === "string" && typeof maybeError.message === "string";
}

export async function requestJson<T>(
  path: string,
  init?: RequestInit
): Promise<T> {
  const url = `${API_BASE_URL}${path}`;
  let response: Response;
  try {
    response = await fetch(url, {
      ...init,
      headers: {
        "Content-Type": "application/json",
        ...(init?.headers ?? {})
      }
    });
  } catch (error) {
    const message =
      error instanceof Error ? error.message : "Network request failed";
    throw new ApiClientError(message, 0, "network_error");
  }

  const text = await response.text();
  let data: unknown = null;
  if (text) {
    try {
      data = JSON.parse(text) as unknown;
    } catch {
      data = text;
    }
  }

  if (!response.ok) {
    if (isApiErrorEnvelope(data)) {
      throw new ApiClientError(
        data.error.message,
        response.status,
        data.error.code,
        data.error.details
      );
    }
    throw new ApiClientError(
      typeof data === "string" && data.trim().length > 0
        ? data
        : `HTTP ${response.status} request failed`,
      response.status,
      "http_error"
    );
  }

  if (data === null) {
    throw new ApiClientError("Empty response body", response.status, "empty_response");
  }
  if (typeof data === "string") {
    throw new ApiClientError("Expected JSON response body", response.status, "invalid_json");
  }

  return data as T;
}
