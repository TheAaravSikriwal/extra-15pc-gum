// The panel's head, the same in both modes: what it's showing in capitals, a verdict where
// there is one, and a few numbers in a grid.
export function Readout({ title, rows, verdict }: { title: string; rows: [string, string][]; verdict?: string | null }) {
  return (
    <header className="readout">
      <div className="readout-title">
        <span>{title}</span>
        {verdict && <span className={`verdict ${verdict === "pass" ? "pass" : "fail"}`}>{verdict}</span>}
      </div>
      {rows.length > 0 && (
        <dl>
          {rows.map(([k, v]) => (
            <div key={k}>
              <dt>{k}</dt>
              <dd>{v}</dd>
            </div>
          ))}
        </dl>
      )}
    </header>
  );
}
