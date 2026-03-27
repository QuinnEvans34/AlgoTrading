import type { StrategyTradeRow } from "../../lib/api/types";
import { formatDateTime } from "../../lib/results/formatters";

interface TradeTableProps {
  trades: StrategyTradeRow[];
}

export function TradeTable({ trades }: TradeTableProps) {
  return (
    <section className="result-panel">
      <h2>Trade Ledger</h2>
      {trades.length === 0 ? (
        <p>No closed trades available for this run.</p>
      ) : (
        <table className="data-table">
          <thead>
            <tr>
              <th>Entry</th>
              <th>Exit</th>
              <th>Side</th>
              <th>Net PnL</th>
              <th>Return %</th>
              <th>Bars</th>
              <th>Exit Reason</th>
            </tr>
          </thead>
          <tbody>
            {trades.map((trade) => (
              <tr key={`${trade.entry_time}-${trade.exit_time}-${trade.direction}`}>
                <td>{formatDateTime(trade.entry_time)}</td>
                <td>{formatDateTime(trade.exit_time)}</td>
                <td>{trade.direction}</td>
                <td>{trade.net_pnl.toFixed(2)}</td>
                <td>{trade.return_pct.toFixed(2)}</td>
                <td>{trade.bars_held}</td>
                <td>{trade.exit_reason}</td>
              </tr>
            ))}
          </tbody>
        </table>
      )}
    </section>
  );
}
