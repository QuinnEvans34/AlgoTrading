import { Link } from "react-router-dom";

export function RunsPage() {
  return (
    <section className="page">
      <h2>Legacy Stored Runs Route</h2>
      <p>
        The primary run browser is now <Link to="/history">Run History</Link>,
        with compare support under <Link to="/compare">Compare Runs</Link>.
      </p>
      <section className="result-panel">
        <h2>Quick Links</h2>
        <div className="controls-row">
          <Link to="/history">Open Run History</Link>
          <Link to="/compare">Open Compare Runs</Link>
        </div>
      </section>
    </section>
  );
}
