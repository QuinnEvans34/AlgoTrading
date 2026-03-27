import { useState } from "react";

import type { PriceUpdateRequest } from "../../lib/paperTrading/types";

interface PriceUpdateFormProps {
  isSubmitting: boolean;
  onSubmit: (payload: PriceUpdateRequest) => Promise<void>;
}

export function PriceUpdateForm({ isSubmitting, onSubmit }: PriceUpdateFormProps) {
  const [symbol, setSymbol] = useState("AAPL");
  const [assetClass, setAssetClass] = useState<"stock" | "forex">("stock");
  const [price, setPrice] = useState("100");
  const [localError, setLocalError] = useState<string | null>(null);

  async function handleSubmit(event: React.FormEvent<HTMLFormElement>) {
    event.preventDefault();
    setLocalError(null);
    if (!symbol.trim()) {
      setLocalError("Symbol is required.");
      return;
    }
    const parsedPrice = Number(price);
    if (!Number.isFinite(parsedPrice) || parsedPrice <= 0) {
      setLocalError("Price must be greater than zero.");
      return;
    }
    await onSubmit({
      instrument: {
        symbol: symbol.trim().toUpperCase(),
        asset_class: assetClass
      },
      price: parsedPrice,
      source: "manual"
    });
  }

  return (
    <form className="run-form" onSubmit={handleSubmit}>
      <section className="form-section">
        <h3>Process Price Update</h3>
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
          <span>Mark Price</span>
          <input
            type="number"
            min={0.000001}
            step="0.000001"
            value={price}
            onChange={(event) => setPrice(event.target.value)}
          />
        </label>
      </section>
      {localError ? <p className="local-error">{localError}</p> : null}
      <button type="submit" disabled={isSubmitting}>
        {isSubmitting ? "Applying..." : "Apply Price Update"}
      </button>
    </form>
  );
}

