import type { PaperFill } from "../../lib/paperTrading/types";

interface FillsTableProps {
  fills: PaperFill[];
}

function formatNumber(value: number | null | undefined): string {
  if (value === null || value === undefined || Number.isNaN(value)) {
    return "n/a";
  }
  return value.toFixed(4);
}

export function FillsTable({ fills }: FillsTableProps) {
  return (
    <section className="result-panel">
      <h2>Recent Fills</h2>
      {fills.length === 0 ? <p>No fills yet.</p> : null}
      {fills.length > 0 ? (
        <table className="data-table compact">
          <thead>
            <tr>
              <th>Time</th>
              <th>Fill ID</th>
              <th>Order ID</th>
              <th>Symbol</th>
              <th>Side</th>
              <th>Qty</th>
              <th>Price</th>
              <th>Commission</th>
              <th>Realized Δ</th>
            </tr>
          </thead>
          <tbody>
            {fills.map((fill) => (
              <tr key={fill.fill_id}>
                <td>{new Date(fill.timestamp).toLocaleString()}</td>
                <td>{fill.fill_id}</td>
                <td>{fill.order_id}</td>
                <td>{fill.instrument.symbol}</td>
                <td>{fill.side}</td>
                <td>{formatNumber(fill.quantity)}</td>
                <td>{formatNumber(fill.fill_price)}</td>
                <td>{formatNumber(fill.commission)}</td>
                <td>{formatNumber(fill.realized_pnl_delta)}</td>
              </tr>
            ))}
          </tbody>
        </table>
      ) : null}
    </section>
  );
}

