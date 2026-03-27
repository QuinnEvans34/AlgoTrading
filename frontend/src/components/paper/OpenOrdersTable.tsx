import type { PaperOrder } from "../../lib/paperTrading/types";

interface OpenOrdersTableProps {
  orders: PaperOrder[];
  isSubmitting: boolean;
  onCancel: (orderId: string) => Promise<void>;
}

function formatNumber(value: number | null | undefined): string {
  if (value === null || value === undefined || Number.isNaN(value)) {
    return "n/a";
  }
  return value.toFixed(4);
}

export function OpenOrdersTable({
  orders,
  isSubmitting,
  onCancel
}: OpenOrdersTableProps) {
  return (
    <section className="result-panel">
      <h2>Open Orders</h2>
      {orders.length === 0 ? <p>No open orders.</p> : null}
      {orders.length > 0 ? (
        <table className="data-table compact">
          <thead>
            <tr>
              <th>Order ID</th>
              <th>Symbol</th>
              <th>Side</th>
              <th>Type</th>
              <th>Quantity</th>
              <th>Limit Price</th>
              <th>Created</th>
              <th>Action</th>
            </tr>
          </thead>
          <tbody>
            {orders.map((order) => (
              <tr key={order.order_id}>
                <td>{order.order_id}</td>
                <td>{order.instrument.symbol}</td>
                <td>{order.side}</td>
                <td>{order.order_type}</td>
                <td>{formatNumber(order.quantity)}</td>
                <td>{formatNumber(order.limit_price ?? null)}</td>
                <td>{new Date(order.created_at).toLocaleString()}</td>
                <td>
                  <button
                    type="button"
                    disabled={isSubmitting}
                    onClick={() => void onCancel(order.order_id)}
                  >
                    Cancel
                  </button>
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      ) : null}
    </section>
  );
}

