import { useEffect, useState } from "react";

import { ErrorAlert } from "../components/common/ErrorAlert";
import { LoadingState } from "../components/common/LoadingState";
import { FillsTable } from "../components/paper/FillsTable";
import { OpenOrdersTable } from "../components/paper/OpenOrdersTable";
import { OpenPositionsTable } from "../components/paper/OpenPositionsTable";
import { PaperAccountSummary } from "../components/paper/PaperAccountSummary";
import { PaperOrderForm } from "../components/paper/PaperOrderForm";
import { PriceUpdateForm } from "../components/paper/PriceUpdateForm";
import {
  cancelPaperOrder,
  fetchPaperState,
  placePaperOrder,
  processPaperPriceUpdate,
  resetPaperAccount
} from "../lib/paperTrading/api";
import type {
  PaperOrderRequest,
  PaperStateResponse,
  PriceUpdateRequest
} from "../lib/paperTrading/types";

export function PaperTradingPage() {
  const [state, setState] = useState<PaperStateResponse | null>(null);
  const [loading, setLoading] = useState(false);
  const [submitting, setSubmitting] = useState(false);
  const [error, setError] = useState<unknown>(null);

  useEffect(() => {
    async function load() {
      setLoading(true);
      setError(null);
      try {
        const response = await fetchPaperState(200);
        setState(response);
      } catch (err) {
        setError(err);
      } finally {
        setLoading(false);
      }
    }
    void load();
  }, []);

  async function submitOrder(payload: PaperOrderRequest) {
    setSubmitting(true);
    setError(null);
    try {
      const result = await placePaperOrder(payload);
      setState(result.state);
    } catch (err) {
      setError(err);
    } finally {
      setSubmitting(false);
    }
  }

  async function submitPriceUpdate(payload: PriceUpdateRequest) {
    setSubmitting(true);
    setError(null);
    try {
      const result = await processPaperPriceUpdate(payload);
      setState(result.state);
    } catch (err) {
      setError(err);
    } finally {
      setSubmitting(false);
    }
  }

  async function cancelOrder(orderId: string) {
    setSubmitting(true);
    setError(null);
    try {
      const result = await cancelPaperOrder(orderId);
      setState(result.state);
    } catch (err) {
      setError(err);
    } finally {
      setSubmitting(false);
    }
  }

  async function resetAccount() {
    setSubmitting(true);
    setError(null);
    try {
      const response = await resetPaperAccount({});
      setState(response);
    } catch (err) {
      setError(err);
    } finally {
      setSubmitting(false);
    }
  }

  return (
    <section className="page">
      <h2>Paper Trading Sandbox</h2>
      <p>
        Place manual paper orders, apply price updates, and track simulated account
        state without touching live brokers.
      </p>

      <section className="result-panel">
        <h2>Actions</h2>
        <div className="controls-row">
          <button type="button" disabled={submitting} onClick={() => void resetAccount()}>
            Reset Account
          </button>
          <button
            type="button"
            disabled={loading || submitting}
            onClick={() => {
              void (async () => {
                try {
                  setLoading(true);
                  const response = await fetchPaperState(200);
                  setState(response);
                } catch (err) {
                  setError(err);
                } finally {
                  setLoading(false);
                }
              })();
            }}
          >
            Refresh State
          </button>
        </div>
      </section>

      {loading ? <LoadingState label="Loading paper account state..." /> : null}
      {error ? <ErrorAlert error={error} /> : null}

      <PaperOrderForm isSubmitting={submitting} onSubmit={submitOrder} />
      <PriceUpdateForm isSubmitting={submitting} onSubmit={submitPriceUpdate} />

      {state ? (
        <>
          <PaperAccountSummary state={state} />
          <OpenPositionsTable positions={state.positions} />
          <OpenOrdersTable
            orders={state.open_orders}
            isSubmitting={submitting}
            onCancel={cancelOrder}
          />
          <FillsTable fills={state.fills} />
        </>
      ) : null}
    </section>
  );
}

