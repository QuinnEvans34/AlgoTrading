import type { StepResult } from "../../lib/api/types";

interface StepResultsTableProps {
  steps: StepResult[];
}

export function StepResultsTable({ steps }: StepResultsTableProps) {
  if (steps.length === 0) {
    return (
      <section className="result-panel">
        <h2>Step Timeline</h2>
        <p>No steps returned.</p>
      </section>
    );
  }

  return (
    <section className="result-panel">
      <h2>Step Timeline</h2>
      <table className="steps-table">
        <thead>
          <tr>
            <th>Step</th>
            <th>Status</th>
            <th>Duration (ms)</th>
            <th>Error</th>
          </tr>
        </thead>
        <tbody>
          {steps.map((step) => (
            <tr key={`${step.step_name}-${step.started_at}`}>
              <td>{step.step_name}</td>
              <td>
                <span className={`step-badge ${step.status}`}>{step.status}</span>
              </td>
              <td>{step.duration_ms}</td>
              <td>{step.error_message ?? "-"}</td>
            </tr>
          ))}
        </tbody>
      </table>
    </section>
  );
}

