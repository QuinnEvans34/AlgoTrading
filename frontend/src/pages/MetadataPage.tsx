import { useEffect, useState } from "react";

import { ErrorAlert } from "../components/common/ErrorAlert";
import { LoadingState } from "../components/common/LoadingState";
import { fetchCapabilities } from "../lib/api/metadata";
import type { CapabilitiesResponse } from "../lib/api/types";

export function MetadataPage() {
  const [data, setData] = useState<CapabilitiesResponse | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<unknown>(null);

  async function refresh() {
    setLoading(true);
    setError(null);
    try {
      const response = await fetchCapabilities();
      setData(response);
    } catch (err) {
      setError(err);
    } finally {
      setLoading(false);
    }
  }

  useEffect(() => {
    void refresh();
  }, []);

  return (
    <section className="page">
      <h2>Backend Capabilities</h2>
      <p>
        Provider, strategy, workflow, and model metadata comes from{" "}
        <code>/metadata/capabilities</code>.
      </p>
      <button type="button" onClick={() => void refresh()} disabled={loading}>
        {loading ? "Refreshing..." : "Refresh Capabilities"}
      </button>

      {loading ? <LoadingState label="Loading capabilities..." /> : null}
      {error ? <ErrorAlert error={error} /> : null}

      {data ? (
        <div className="card-grid">
          <Card title="Workflows" items={data.workflows} />
          <Card title="Strategies" items={data.strategies} />
          <Card title="Providers" items={data.providers} />
          <Card title="Intervals" items={data.intervals} />
          <Card title="Asset Classes" items={data.asset_classes} />
          <Card title="Model Families" items={data.model_families} />
          <Card
            title="Paper Order Types"
            items={data.paper_trading?.supported_order_types ?? []}
          />
          <Card
            title="Live Broker"
            items={
              data.live_execution
                ? [
                    `broker=${data.live_execution.broker_name}`,
                    `state=${data.live_execution.state}`,
                    `enabled=${String(data.live_execution.enabled)}`
                  ]
                : []
            }
          />
          <Card
            title="Live Order Types"
            items={data.live_execution?.supported_order_types ?? []}
          />
        </div>
      ) : null}
    </section>
  );
}

interface CardProps {
  title: string;
  items: string[];
}

function Card({ title, items }: CardProps) {
  return (
    <section className="result-panel">
      <h3>{title}</h3>
      {items.length === 0 ? (
        <p>No values returned.</p>
      ) : (
        <ul className="simple-list">
          {items.map((item) => (
            <li key={item}>{item}</li>
          ))}
        </ul>
      )}
    </section>
  );
}
