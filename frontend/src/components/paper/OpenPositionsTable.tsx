import type { PaperPosition } from "../../lib/paperTrading/types";

interface OpenPositionsTableProps {
  positions: PaperPosition[];
}

function formatNumber(value: number | null | undefined): string {
  if (value === null || value === undefined || Number.isNaN(value)) {
    return "n/a";
  }
  return value.toFixed(4);
}

export function OpenPositionsTable({ positions }: OpenPositionsTableProps) {
  return (
    <section className="result-panel">
      <h2>Open Positions</h2>
      {positions.length === 0 ? <p>No open positions.</p> : null}
      {positions.length > 0 ? (
        <table className="data-table compact">
          <thead>
            <tr>
              <th>Symbol</th>
              <th>Asset</th>
              <th>Quantity</th>
              <th>Avg Price</th>
              <th>Mark Price</th>
              <th>Unrealized PnL</th>
              <th>Realized PnL</th>
            </tr>
          </thead>
          <tbody>
            {positions.map((position) => (
              <tr key={position.instrument.symbol}>
                <td>{position.instrument.symbol}</td>
                <td>{position.instrument.asset_class}</td>
                <td>{formatNumber(position.quantity)}</td>
                <td>{formatNumber(position.average_price)}</td>
                <td>{formatNumber(position.mark_price ?? null)}</td>
                <td>{formatNumber(position.unrealized_pnl)}</td>
                <td>{formatNumber(position.realized_pnl)}</td>
              </tr>
            ))}
          </tbody>
        </table>
      ) : null}
    </section>
  );
}

