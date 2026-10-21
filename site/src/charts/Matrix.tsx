// The pass/fail matrix: every scenario against every combination, like the flight sim report's.
export type Cell = "pass" | "fail" | "not yet" | "";

export interface MatrixProps {
  title: string;
  rows: string[]; // the scenarios
  columns: string[]; // the combinations
  cell: (row: string, column: string) => Cell;
  link?: (row: string, column: string) => string | undefined;
}

export function Matrix(p: MatrixProps) {
  return (
    <table className="matrix" aria-label={p.title}>
      <thead>
        <tr>
          <th scope="col">Scenario</th>
          {p.columns.map((c) => (
            <th key={c} scope="col">
              {c}
            </th>
          ))}
        </tr>
      </thead>
      <tbody>
        {p.rows.map((r) => (
          <tr key={r}>
            <th scope="row">{r}</th>
            {p.columns.map((c) => {
              const value = p.cell(r, c);
              const href = value === "pass" || value === "fail" ? p.link?.(r, c) : undefined;
              return (
                <td key={c} className={value.replace(" ", "-") || "blank"}>
                  {href ? <a href={href}>{value}</a> : value}
                </td>
              );
            })}
          </tr>
        ))}
      </tbody>
    </table>
  );
}
