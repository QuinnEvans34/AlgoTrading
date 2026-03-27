import type { LiveExecutionReadinessResponse } from "../../lib/liveExecution/types";

interface LiveGuardrailPanelProps {
  readiness: LiveExecutionReadinessResponse | null;
}

export function LiveGuardrailPanel({ readiness }: LiveGuardrailPanelProps) {
  if (!readiness) {
    return null;
  }

  return (
    <section className="result-panel">
      <h3>Guardrail Checks</h3>
      <table className="data-table compact">
        <thead>
          <tr>
            <th>Check</th>
            <th>Pass</th>
            <th>Code</th>
            <th>Message</th>
          </tr>
        </thead>
        <tbody>
          {readiness.checks.map((check) => (
            <tr key={check.name}>
              <td>{check.name}</td>
              <td>{check.passed ? "Yes" : "No"}</td>
              <td>{check.code ?? "n/a"}</td>
              <td>{check.message}</td>
            </tr>
          ))}
        </tbody>
      </table>
    </section>
  );
}
