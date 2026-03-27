interface FeatureImportancePanelProps {
  items: Array<{ feature: string; score: number }>;
}

export function FeatureImportancePanel({ items }: FeatureImportancePanelProps) {
  return (
    <section className="result-panel">
      <h2>Feature Importance</h2>
      {items.length === 0 ? (
        <p>No feature-importance output available for this run.</p>
      ) : (
        <table className="data-table compact">
          <thead>
            <tr>
              <th>Feature</th>
              <th>Score</th>
            </tr>
          </thead>
          <tbody>
            {items.map((item) => (
              <tr key={item.feature}>
                <td>{item.feature}</td>
                <td>{item.score.toFixed(6)}</td>
              </tr>
            ))}
          </tbody>
        </table>
      )}
    </section>
  );
}
