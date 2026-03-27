import type { PaperStateResponse } from "../../lib/paperTrading/types";

interface PaperAccountSummaryProps {
  state: PaperStateResponse;
}

function formatNumber(value: number): string {
  return value.toFixed(2);
}

export function PaperAccountSummary({ state }: PaperAccountSummaryProps) {
  const account = state.account;
  return (
    <section className="result-panel">
      <h2>Paper Account</h2>
      <div className="summary-grid">
        <div className="info-item">
          <span>Account ID</span>
          <strong>{account.account_id}</strong>
        </div>
        <div className="info-item">
          <span>Cash</span>
          <strong>{formatNumber(account.cash)}</strong>
        </div>
        <div className="info-item">
          <span>Equity</span>
          <strong>{formatNumber(account.equity)}</strong>
        </div>
        <div className="info-item">
          <span>Realized PnL</span>
          <strong>{formatNumber(account.realized_pnl)}</strong>
        </div>
        <div className="info-item">
          <span>Unrealized PnL</span>
          <strong>{formatNumber(account.unrealized_pnl)}</strong>
        </div>
        <div className="info-item">
          <span>Total Fees</span>
          <strong>{formatNumber(account.total_fees)}</strong>
        </div>
        <div className="info-item">
          <span>Open Orders</span>
          <strong>{state.open_orders.length}</strong>
        </div>
        <div className="info-item">
          <span>Open Positions</span>
          <strong>{state.positions.length}</strong>
        </div>
      </div>
    </section>
  );
}

