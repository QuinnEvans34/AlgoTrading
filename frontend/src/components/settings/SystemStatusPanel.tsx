import { API_BASE_URL, FRONTEND_ENV } from "../../lib/config";
import type { ProviderStatus, RuntimeStatus, StorageStatus } from "../../lib/settings/types";

interface SystemStatusPanelProps {
  runtime: RuntimeStatus;
  storage: StorageStatus;
  providers: ProviderStatus;
}

export function SystemStatusPanel({ runtime, storage, providers }: SystemStatusPanelProps) {
  return (
    <section className="result-panel">
      <h3>System Runtime</h3>
      <div className="summary-grid">
        <div className="info-item">
          <span>Backend App</span>
          <strong>{runtime.app_name}</strong>
        </div>
        <div className="info-item">
          <span>API Prefix</span>
          <strong>{runtime.api_prefix}</strong>
        </div>
        <div className="info-item">
          <span>Backend Host:Port</span>
          <strong>
            {runtime.host}:{runtime.port}
          </strong>
        </div>
        <div className="info-item">
          <span>Frontend Env</span>
          <strong>{FRONTEND_ENV}</strong>
        </div>
        <div className="info-item">
          <span>Frontend API Base URL</span>
          <strong>{API_BASE_URL}</strong>
        </div>
        <div className="info-item">
          <span>Generated At</span>
          <strong>{new Date(runtime.generated_at).toLocaleString()}</strong>
        </div>
      </div>

      <h4>Storage Paths</h4>
      <div className="summary-grid">
        <div className="info-item">
          <span>Run Artifacts</span>
          <strong>{storage.run_output_dir}</strong>
        </div>
        <div className="info-item">
          <span>Paper Trading State</span>
          <strong>{storage.paper_trading_dir}</strong>
        </div>
      </div>

      <h4>Provider Readiness</h4>
      <div className="summary-grid">
        <div className="info-item">
          <span>OANDA Market Data Enabled</span>
          <strong>{providers.oanda_market_data_enabled ? "Yes" : "No"}</strong>
        </div>
        <div className="info-item">
          <span>OANDA Market Data Configured</span>
          <strong>{providers.oanda_market_data_configured ? "Yes" : "No"}</strong>
        </div>
        <div className="info-item">
          <span>OANDA Live Configured</span>
          <strong>{providers.live_oanda_configured ? "Yes" : "No"}</strong>
        </div>
      </div>
    </section>
  );
}

