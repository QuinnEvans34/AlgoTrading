import type { AssetClass, Instrument } from "../api/types";

export type PaperOrderSide = "buy" | "sell";
export type PaperOrderType = "market" | "limit";
export type PaperOrderStatus = "open" | "filled" | "cancelled" | "rejected";

export interface PaperAccountConfig {
  account_id: string;
  base_currency: string;
  initial_cash: number;
  allow_short: boolean;
  default_spread_bps: number;
  default_slippage_bps: number;
  commission_bps: number;
  commission_fixed: number;
}

export interface PaperAccountState {
  account_id: string;
  base_currency: string;
  cash: number;
  realized_pnl: number;
  unrealized_pnl: number;
  equity: number;
  total_fees: number;
  updated_at: string;
}

export interface PaperPosition {
  instrument: Instrument;
  quantity: number;
  average_price: number;
  mark_price?: number | null;
  unrealized_pnl: number;
  realized_pnl: number;
  updated_at: string;
}

export interface PaperOrder {
  order_id: string;
  instrument: Instrument;
  side: PaperOrderSide;
  order_type: PaperOrderType;
  quantity: number;
  status: PaperOrderStatus;
  created_at: string;
  updated_at: string;
  limit_price?: number | null;
  reference_price?: number | null;
  client_order_id?: string | null;
  rejection_reason?: string | null;
  filled_quantity: number;
  average_fill_price?: number | null;
  metadata: Record<string, unknown>;
}

export interface PaperFill {
  fill_id: string;
  order_id: string;
  instrument: Instrument;
  side: PaperOrderSide;
  quantity: number;
  fill_price: number;
  notional: number;
  commission: number;
  spread_cost: number;
  slippage_cost: number;
  realized_pnl_delta: number;
  timestamp: string;
}

export interface PaperStateResponse {
  config: PaperAccountConfig;
  account: PaperAccountState;
  positions: PaperPosition[];
  open_orders: PaperOrder[];
  fills: PaperFill[];
  price_book: Record<string, number>;
  updated_at: string;
}

export interface PaperOrderRequest {
  instrument: Instrument;
  side: PaperOrderSide;
  order_type: PaperOrderType;
  quantity: number;
  limit_price?: number;
  reference_price?: number;
  client_order_id?: string;
  metadata?: Record<string, unknown>;
}

export interface PaperOrderActionResponse {
  order: PaperOrder;
  fills: PaperFill[];
  state: PaperStateResponse;
}

export interface PaperCancelActionResponse {
  order: PaperOrder;
  state: PaperStateResponse;
}

export interface PriceUpdateRequest {
  instrument: Instrument;
  price: number;
  timestamp?: string;
  source?: string;
}

export interface PaperPriceUpdateResponse {
  filled_order_ids: string[];
  state: PaperStateResponse;
}

export interface PaperSignalIntentRequest {
  instrument: Instrument;
  direction: PaperOrderSide;
  quantity: number;
  reference_price?: number;
  client_order_id?: string;
  metadata?: Record<string, unknown>;
}

export interface PaperResetRequest {
  account_id?: string;
  base_currency?: string;
  initial_cash?: number;
  allow_short?: boolean;
  default_spread_bps?: number;
  default_slippage_bps?: number;
  commission_bps?: number;
  commission_fixed?: number;
}

export interface PaperTradingCapabilities {
  supported_order_types: string[];
  supported_order_sides: string[];
  supports_short: boolean;
  supports_signal_intents: boolean;
  supported_asset_classes: AssetClass[];
}

