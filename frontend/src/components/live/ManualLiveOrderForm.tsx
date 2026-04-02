import { useMemo, useState } from "react";

import type {
  LiveExecutionReadinessResponse,
  LiveOrderSide,
  LiveOrderType,
  LiveTradeIntentRequest,
  ManualLiveOrderRequest
} from "../../lib/liveExecution/types";

interface ManualLiveOrderFormProps {
  readiness: LiveExecutionReadinessResponse | null;
  submitting: boolean;
  onValidate: (intent: LiveTradeIntentRequest) => Promise<void>;
  onSubmit: (request: ManualLiveOrderRequest) => Promise<void>;
}

interface FormState {
  symbol: string;
  assetClass: "stock" | "forex";
  side: LiveOrderSide;
  orderType: LiveOrderType;
  quantity: number;
  limitPrice: string;
  clientOrderId: string;
  idempotencyKey: string;
  confirmLiveExecution: boolean;
  confirmationText: string;
  operatorId: string;
  operatorNote: string;
}

const DEFAULT_FORM: FormState = {
  symbol: "EUR_USD",
  assetClass: "forex",
  side: "buy",
  orderType: "market",
  quantity: 1000,
  limitPrice: "",
  clientOrderId: "",
  idempotencyKey: `idem-${Date.now()}`,
  confirmLiveExecution: false,
  confirmationText: "",
  operatorId: "",
  operatorNote: ""
};

export function ManualLiveOrderForm({
  readiness,
  submitting,
  onValidate,
  onSubmit
}: ManualLiveOrderFormProps) {
  const [form, setForm] = useState<FormState>(DEFAULT_FORM);

  const liveIntent = useMemo<LiveTradeIntentRequest>(() => {
    const intent: LiveTradeIntentRequest = {
      instrument: {
        symbol: form.symbol.trim(),
        asset_class: form.assetClass
      },
      side: form.side,
      order_type: form.orderType,
      quantity: Number(form.quantity),
      metadata: {
        source: "frontend-manual-live-order"
      }
    };
    if (form.orderType === "limit" && form.limitPrice.trim() !== "") {
      intent.limit_price = Number(form.limitPrice);
    }
    if (form.clientOrderId.trim() !== "") {
      intent.client_order_id = form.clientOrderId.trim();
    }
    return intent;
  }, [form]);

  const request = useMemo<ManualLiveOrderRequest>(() => {
    return {
      intent: liveIntent,
      idempotency_key: form.idempotencyKey.trim(),
      confirm_live_execution: form.confirmLiveExecution,
      confirmation_text: form.confirmationText,
      operator_id: form.operatorId.trim() || undefined,
      operator_note: form.operatorNote.trim() || undefined
    };
  }, [form, liveIntent]);

  return (
    <section className="run-form">
      <h3>Manual Live Order</h3>
      <p>
        Manual-only submission. Automated strategy-to-live execution is not supported in
        this phase.
      </p>

      <div className="field-inline">
        <span>Symbol</span>
        <input
          aria-label="Live Symbol"
          value={form.symbol}
          onChange={(event) => setForm((prev) => ({ ...prev, symbol: event.target.value }))}
        />
      </div>
      <div className="field-inline">
        <span>Asset Class</span>
        <select
          aria-label="Live Asset Class"
          value={form.assetClass}
          onChange={(event) =>
            setForm((prev) => ({
              ...prev,
              assetClass: event.target.value as "stock" | "forex"
            }))
          }
        >
          <option value="forex">forex</option>
          <option value="stock">stock</option>
        </select>
      </div>
      <div className="field-inline">
        <span>Side</span>
        <select
          aria-label="Live Side"
          value={form.side}
          onChange={(event) =>
            setForm((prev) => ({ ...prev, side: event.target.value as LiveOrderSide }))
          }
        >
          <option value="buy">buy</option>
          <option value="sell">sell</option>
        </select>
      </div>
      <div className="field-inline">
        <span>Order Type</span>
        <select
          aria-label="Live Order Type"
          value={form.orderType}
          onChange={(event) =>
            setForm((prev) => ({ ...prev, orderType: event.target.value as LiveOrderType }))
          }
        >
          <option value="market">market</option>
          <option value="limit">limit</option>
        </select>
      </div>
      <div className="field-inline">
        <span>Quantity</span>
        <input
          aria-label="Live Quantity"
          type="number"
          min={0}
          value={form.quantity}
          onChange={(event) =>
            setForm((prev) => ({ ...prev, quantity: Number(event.target.value) }))
          }
        />
      </div>
      <div className="field-inline">
        <span>Limit Price</span>
        <input
          aria-label="Live Limit Price"
          type="number"
          min={0}
          value={form.limitPrice}
          placeholder={form.orderType === "limit" ? "Required for limit order" : "n/a"}
          onChange={(event) => setForm((prev) => ({ ...prev, limitPrice: event.target.value }))}
        />
      </div>
      <div className="field-inline">
        <span>Client Order Id</span>
        <input
          aria-label="Live Client Order ID"
          value={form.clientOrderId}
          onChange={(event) =>
            setForm((prev) => ({ ...prev, clientOrderId: event.target.value }))
          }
        />
      </div>
      <div className="field-inline">
        <span>Idempotency Key</span>
        <input
          aria-label="Live Idempotency Key"
          value={form.idempotencyKey}
          onChange={(event) =>
            setForm((prev) => ({ ...prev, idempotencyKey: event.target.value }))
          }
        />
      </div>
      <div className="field-inline">
        <span>Operator Id</span>
        <input
          aria-label="Live Operator ID"
          value={form.operatorId}
          onChange={(event) => setForm((prev) => ({ ...prev, operatorId: event.target.value }))}
        />
      </div>
      <div className="field-inline">
        <span>Operator Note</span>
        <input
          aria-label="Live Operator Note"
          value={form.operatorNote}
          onChange={(event) => setForm((prev) => ({ ...prev, operatorNote: event.target.value }))}
        />
      </div>
      <div className="field-inline checkbox-row">
        <input
          type="checkbox"
          aria-label="Confirm live execution"
          checked={form.confirmLiveExecution}
          onChange={(event) =>
            setForm((prev) => ({
              ...prev,
              confirmLiveExecution: event.target.checked
            }))
          }
        />
        <span>I confirm this is a manual live order attempt.</span>
      </div>
      <div className="field-inline">
        <span>Confirmation Text</span>
        <input
          aria-label="Live Confirmation Text"
          value={form.confirmationText}
          placeholder={readiness?.confirmation_phrase ?? "EXECUTE LIVE ORDER"}
          onChange={(event) =>
            setForm((prev) => ({ ...prev, confirmationText: event.target.value }))
          }
        />
      </div>

      <div className="controls-row">
        <button type="button" disabled={submitting} onClick={() => void onValidate(liveIntent)}>
          Validate Intent
        </button>
        <button type="button" disabled={submitting} onClick={() => void onSubmit(request)}>
          Submit Manual Order
        </button>
      </div>
    </section>
  );
}
