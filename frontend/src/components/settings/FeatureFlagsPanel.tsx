import type { FeatureFlagsStatus } from "../../lib/settings/types";

interface FeatureFlagsPanelProps {
  flags: FeatureFlagsStatus;
}

export function FeatureFlagsPanel({ flags }: FeatureFlagsPanelProps) {
  const rows: Array<{ name: string; enabled: boolean }> = [
    { name: "research_api_enabled", enabled: flags.research_api_enabled },
    { name: "history_api_enabled", enabled: flags.history_api_enabled },
    { name: "compare_api_enabled", enabled: flags.compare_api_enabled },
    { name: "paper_trading_enabled", enabled: flags.paper_trading_enabled },
    {
      name: "live_execution_status_enabled",
      enabled: flags.live_execution_status_enabled
    },
    {
      name: "live_execution_submit_enabled",
      enabled: flags.live_execution_submit_enabled
    }
  ];

  return (
    <section className="result-panel">
      <h3>Feature Flags</h3>
      <table className="data-table compact">
        <thead>
          <tr>
            <th>Flag</th>
            <th>Enabled</th>
          </tr>
        </thead>
        <tbody>
          {rows.map((row) => (
            <tr key={row.name}>
              <td>
                <code>{row.name}</code>
              </td>
              <td>{row.enabled ? "true" : "false"}</td>
            </tr>
          ))}
        </tbody>
      </table>
    </section>
  );
}

