import type { PaperDefaultsStatus } from "../../lib/settings/types";

interface PaperTradingSettingsPanelProps {
  defaults: PaperDefaultsStatus;
}

export function PaperTradingSettingsPanel({ defaults }: PaperTradingSettingsPanelProps) {
  return (
    <section className="result-panel">
      <h3>Paper Trading Defaults</h3>
      <div className="summary-grid">
        <div className="info-item">
          <span>Account ID</span>
          <strong>{defaults.account_id}</strong>
        </div>
        <div className="info-item">
          <span>Base Currency</span>
          <strong>{defaults.base_currency}</strong>
        </div>
        <div className="info-item">
          <span>Initial Cash</span>
          <strong>{defaults.initial_cash.toLocaleString()}</strong>
        </div>
        <div className="info-item">
          <span>Allow Short</span>
          <strong>{defaults.allow_short ? "Yes" : "No"}</strong>
        </div>
        <div className="info-item">
          <span>Spread (bps)</span>
          <strong>{defaults.spread_bps}</strong>
        </div>
        <div className="info-item">
          <span>Slippage (bps)</span>
          <strong>{defaults.slippage_bps}</strong>
        </div>
        <div className="info-item">
          <span>Commission (bps)</span>
          <strong>{defaults.commission_bps}</strong>
        </div>
        <div className="info-item">
          <span>Commission (fixed)</span>
          <strong>{defaults.commission_fixed}</strong>
        </div>
      </div>
    </section>
  );
}

