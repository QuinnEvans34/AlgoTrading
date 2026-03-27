import type { AssetClass, Instrument } from "../api/types";

export type LiveBrokerName = "null" | "oanda_stub";
export type LiveOrderSide = "buy" | "sell";
export type LiveOrderType = "market" | "limit";
export type LiveConnectionState = "disabled" | "not_configured" | "ready" | "error";

export interface LiveExecutionCapabilities {
  supported_asset_classes: AssetClass[];
  supported_order_types: LiveOrderType[];
  supported_order_sides: LiveOrderSide[];
  supports_short: boolean;
  supports_cancel: boolean;
  supports_submit: boolean;
}

export interface LiveExecutionStatusResponse {
  broker_name: LiveBrokerName;
  configured: boolean;
  enabled: boolean;
  submission_allowed: boolean;
  state: LiveConnectionState;
  message: string;
  capabilities: LiveExecutionCapabilities;
}

export interface LiveGuardCheck {
  name: string;
  passed: boolean;
  code?: string | null;
  message: string;
}

export interface LiveExecutionReadinessResponse {
  generated_at: string;
  broker_name: LiveBrokerName;
  enabled: boolean;
  submission_allowed: boolean;
  configured: boolean;
  state: LiveConnectionState;
  message: string;
  manual_submission_ready: boolean;
  confirmation_phrase: string;
  checks: LiveGuardCheck[];
}

export interface LiveTradeIntentRequest {
  instrument: Instrument;
  side: LiveOrderSide;
  order_type: LiveOrderType;
  quantity: number;
  limit_price?: number;
  client_order_id?: string;
  metadata?: Record<string, unknown>;
}

export interface ManualLiveOrderRequest {
  intent: LiveTradeIntentRequest;
  idempotency_key: string;
  confirm_live_execution: boolean;
  confirmation_text: string;
  operator_id?: string;
  operator_note?: string;
}

export interface LiveIntentValidationResponse {
  accepted: boolean;
  reasons: string[];
  normalized_intent?: LiveTradeIntentRequest | null;
  broker_payload_preview?: Record<string, unknown> | null;
}

export interface LiveSubmitResponse {
  accepted: boolean;
  status: string;
  reason?: string | null;
  external_order_id?: string | null;
  broker_payload?: Record<string, unknown> | null;
}

export interface ManualLiveSubmitResponse {
  accepted: boolean;
  status: string;
  attempt_id: string;
  broker_name: LiveBrokerName;
  rejection_code?: string | null;
  rejection_message?: string | null;
  external_order_id?: string | null;
  broker_payload?: Record<string, unknown> | null;
  guard_checks: LiveGuardCheck[];
}

export interface LiveExecutionAttemptRecord {
  attempt_id: string;
  timestamp: string;
  broker_name: LiveBrokerName;
  idempotency_key: string;
  request_summary: Record<string, unknown>;
  guard_checks: LiveGuardCheck[];
  accepted: boolean;
  status: string;
  rejection_code?: string | null;
  rejection_message?: string | null;
  external_order_id?: string | null;
}

export interface LiveExecutionAttemptsResponse {
  attempts: LiveExecutionAttemptRecord[];
}
