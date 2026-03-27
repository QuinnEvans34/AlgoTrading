import { useEffect, useState } from "react";

import { ErrorAlert } from "../components/common/ErrorAlert";
import { LoadingState } from "../components/common/LoadingState";
import { FeatureFlagsPanel } from "../components/settings/FeatureFlagsPanel";
import { LiveSafetyPanel } from "../components/settings/LiveSafetyPanel";
import { PaperTradingSettingsPanel } from "../components/settings/PaperTradingSettingsPanel";
import { SystemStatusPanel } from "../components/settings/SystemStatusPanel";
import { fetchSystemSettings } from "../lib/settings/api";
import type { SystemSettingsResponse } from "../lib/settings/types";

export function SettingsPage() {
  const [settings, setSettings] = useState<SystemSettingsResponse | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<unknown>(null);

  async function refresh() {
    setLoading(true);
    setError(null);
    try {
      const response = await fetchSystemSettings();
      setSettings(response);
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
      <h2>System Settings</h2>
      <p>
        Read-only runtime configuration visibility for safe operations. Secrets are
        never exposed.
      </p>

      <button type="button" onClick={() => void refresh()} disabled={loading}>
        {loading ? "Refreshing..." : "Refresh Settings"}
      </button>

      {loading ? <LoadingState label="Loading system settings..." /> : null}
      {error ? <ErrorAlert error={error} /> : null}

      {settings ? (
        <>
          <SystemStatusPanel
            runtime={settings.runtime}
            storage={settings.storage}
            providers={settings.providers}
          />
          <FeatureFlagsPanel flags={settings.feature_flags} />
          <PaperTradingSettingsPanel defaults={settings.paper_defaults} />
          <LiveSafetyPanel safety={settings.live_safety} />
        </>
      ) : null}
    </section>
  );
}

