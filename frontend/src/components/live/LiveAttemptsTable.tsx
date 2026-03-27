import type { LiveExecutionAttemptRecord } from "../../lib/liveExecution/types";

interface LiveAttemptsTableProps {
  attempts: LiveExecutionAttemptRecord[];
}

export function LiveAttemptsTable({ attempts }: LiveAttemptsTableProps) {
  return (
    <section className="result-panel">
      <h3>Recent Live Attempts</h3>
      {attempts.length === 0 ? (
        <p>No attempts recorded yet.</p>
      ) : (
        <table className="data-table compact">
          <thead>
            <tr>
              <th>Time</th>
              <th>Attempt</th>
              <th>Accepted</th>
              <th>Status</th>
              <th>Rejection Code</th>
              <th>Order Id</th>
            </tr>
          </thead>
          <tbody>
            {attempts.map((attempt) => (
              <tr key={attempt.attempt_id}>
                <td>{new Date(attempt.timestamp).toLocaleString()}</td>
                <td>{attempt.attempt_id}</td>
                <td>{attempt.accepted ? "Yes" : "No"}</td>
                <td>{attempt.status}</td>
                <td>{attempt.rejection_code ?? "n/a"}</td>
                <td>{attempt.external_order_id ?? "n/a"}</td>
              </tr>
            ))}
          </tbody>
        </table>
      )}
    </section>
  );
}
