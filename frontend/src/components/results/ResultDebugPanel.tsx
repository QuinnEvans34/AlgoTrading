interface ResultDebugPanelProps {
  title?: string;
  payload: unknown;
}

export function ResultDebugPanel({
  title = "Raw Result Payload",
  payload
}: ResultDebugPanelProps) {
  return (
    <section className="result-panel">
      <details>
        <summary>{title}</summary>
        <pre className="debug-json">{JSON.stringify(payload, null, 2)}</pre>
      </details>
    </section>
  );
}
