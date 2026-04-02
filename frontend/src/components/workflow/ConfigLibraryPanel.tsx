import type { SavedResearchConfigSummary } from "../../lib/workflow/types";

interface ConfigLibraryPanelProps {
  title: string;
  configs: SavedResearchConfigSummary[];
  activeConfigId: string | null;
  saveName: string;
  saveDescription: string;
  busy: boolean;
  onSaveNameChange: (value: string) => void;
  onSaveDescriptionChange: (value: string) => void;
  onSaveNew: () => Promise<void>;
  onUpdateCurrent: () => Promise<void>;
  onLoad: (configId: string) => Promise<void>;
  onDelete: (configId: string) => Promise<void>;
}

export function ConfigLibraryPanel({
  title,
  configs,
  activeConfigId,
  saveName,
  saveDescription,
  busy,
  onSaveNameChange,
  onSaveDescriptionChange,
  onSaveNew,
  onUpdateCurrent,
  onLoad,
  onDelete
}: ConfigLibraryPanelProps) {
  return (
    <section className="result-panel">
      <h2>{title}</h2>
      <label className="field-inline">
        <span>Saved config name</span>
        <input
          aria-label={`${title} name`}
          value={saveName}
          onChange={(event) => onSaveNameChange(event.target.value)}
          placeholder="research-template-v1"
        />
      </label>
      <label className="field-inline">
        <span>Description</span>
        <input
          aria-label={`${title} description`}
          value={saveDescription}
          onChange={(event) => onSaveDescriptionChange(event.target.value)}
          placeholder="Optional note"
        />
      </label>
      <div className="controls-row">
        <button type="button" disabled={busy} onClick={() => void onSaveNew()}>
          Save As New
        </button>
        <button
          type="button"
          disabled={busy || activeConfigId === null}
          onClick={() => void onUpdateCurrent()}
        >
          Update Loaded
        </button>
        {activeConfigId ? <span>Loaded config: {activeConfigId}</span> : <span>No config loaded.</span>}
      </div>

      <div className="nested-panel">
        <h3>Saved Configs</h3>
        {configs.length === 0 ? (
          <p>No saved configs yet.</p>
        ) : (
          <ul className="simple-list">
            {configs.map((config) => (
              <li key={config.id}>
                <strong>{config.name}</strong> ({config.instrument_symbol}, {config.interval})
                <div className="controls-row">
                  <button type="button" disabled={busy} onClick={() => void onLoad(config.id)}>
                    Load
                  </button>
                  <button type="button" disabled={busy} onClick={() => void onDelete(config.id)}>
                    Delete
                  </button>
                </div>
              </li>
            ))}
          </ul>
        )}
      </div>
    </section>
  );
}
