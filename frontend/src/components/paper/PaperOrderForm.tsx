import { useState } from "react";

import type {
  PaperOrderRequest,
  PaperOrderSide,
  PaperOrderType
} from "../../lib/paperTrading/types";

interface PaperOrderFormProps {
  isSubmitting: boolean;
  onSubmit: (payload: PaperOrderRequest) => Promise<void>;
}

export function PaperOrderForm({ isSubmitting, onSubmit }: PaperOrderFormProps) {
  const [symbol, setSymbol] = useState("AAPL");
  const [assetClass, setAssetClass] = useState<"stock" | "forex">("stock");
  const [side, setSide] = useState<PaperOrderSide>("buy");
  const [orderType, setOrderType] = useState<PaperOrderType>("market");
  const [quantity, setQuantity] = useState(10);
  const [limitPrice, setLimitPrice] = useState("");
  const [referencePrice, setReferencePrice] = useState("");
  const [clientOrderId, setClientOrderId] = useState("");
  const [localError, setLocalError] = useState<string | null>(null);

  async function handleSubmit(event: React.FormEvent<HTMLFormElement>) {
    event.preventDefault();
    setLocalError(null);
    if (!symbol.trim()) {
      setLocalError("Symbol is required.");
      return;
    }
    if (quantity <= 0) {
      setLocalError("Quantity must be greater than zero.");
      return;
    }
    if (orderType === "limit" && Number(limitPrice) <= 0) {
      setLocalError("Limit orders require a positive limit price.");
      return;
    }

    const payload: PaperOrderRequest = {
      instrument: {
        symbol: symbol.trim().toUpperCase(),
        asset_class: assetClass
      },
      side,
      order_type: orderType,
      quantity,
      ...(orderType === "limit" ? { limit_price: Number(limitPrice) } : {}),
      ...(referencePrice.trim() ? { reference_price: Number(referencePrice) } : {}),
      ...(clientOrderId.trim() ? { client_order_id: clientOrderId.trim() } : {})
    };
    await onSubmit(payload);
  }

  return (
    <form className="run-form" onSubmit={handleSubmit}>
      <section className="form-section">
        <h3>Place Paper Order</h3>
        <label className="field-inline">
          <span>Symbol</span>
          <input value={symbol} onChange={(event) => setSymbol(event.target.value)} />
        </label>
        <label className="field-inline">
          <span>Asset Class</span>
          <select
            value={assetClass}
            onChange={(event) => setAssetClass(event.target.value as "stock" | "forex")}
          >
            <option value="stock">stock</option>
            <option value="forex">forex</option>
          </select>
        </label>
        <label className="field-inline">
          <span>Side</span>
          <select value={side} onChange={(event) => setSide(event.target.value as PaperOrderSide)}>
            <option value="buy">buy</option>
            <option value="sell">sell</option>
          </select>
        </label>
        <label className="field-inline">
          <span>Order Type</span>
          <select
            value={orderType}
            onChange={(event) => setOrderType(event.target.value as PaperOrderType)}
          >
            <option value="market">market</option>
            <option value="limit">limit</option>
          </select>
        </label>
        <label className="field-inline">
          <span>Quantity</span>
          <input
            type="number"
            min={0.000001}
            step="0.000001"
            value={quantity}
            onChange={(event) => setQuantity(Number(event.target.value))}
          />
        </label>
        {orderType === "limit" ? (
          <label className="field-inline">
            <span>Limit Price</span>
            <input
              type="number"
              min={0.000001}
              step="0.000001"
              value={limitPrice}
              onChange={(event) => setLimitPrice(event.target.value)}
            />
          </label>
        ) : null}
        <label className="field-inline">
          <span>Reference Price (optional)</span>
          <input
            type="number"
            min={0.000001}
            step="0.000001"
            value={referencePrice}
            onChange={(event) => setReferencePrice(event.target.value)}
            placeholder="Needed if no prior mark is available"
          />
        </label>
        <label className="field-inline">
          <span>Client Order ID (optional)</span>
          <input
            value={clientOrderId}
            onChange={(event) => setClientOrderId(event.target.value)}
            placeholder="external-id-123"
          />
        </label>
      </section>
      {localError ? <p className="local-error">{localError}</p> : null}
      <button type="submit" disabled={isSubmitting}>
        {isSubmitting ? "Submitting..." : "Submit Order"}
      </button>
    </form>
  );
}

