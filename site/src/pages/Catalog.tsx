// The catalog: every real part the design chooses from, with every field it has (its specs and
// their sources, thrust tables, dimensions for the CAD, pins and draws for the wiring).
import type { LoadOptions } from "../data/load";
import type { Catalog as CatalogData } from "../data/types";
import { useData } from "../data/useData";
import { money } from "./Build";
import { Tree } from "./Tree";

const TYPES: Record<string, string> = {
  motor: "Motors",
  prop: "Props",
  esc: "ESCs",
  frame: "Frames",
  cell: "Cells",
  component: "Everything else",
  wire: "Wire",
};

export function Catalog({ load }: { load?: LoadOptions }) {
  const { data, problem } = useData<CatalogData>("catalog.json", load);
  if (problem) return <p role="alert">{problem}</p>;
  if (!data) return <p>Loading</p>;
  const types = [...new Set(data.parts.map((p) => p.type))];
  return (
    <main>
      <h1>The catalog</h1>
      <p className="purpose">
        Every real part the design chooses from, {data.parts.length} of them, with every field the catalog holds:
        each number's source, the thrust tables, the shapes the CAD draws, the pins and draws the wiring checks, the
        buy links and the second choices. Open a part to see all of it.
      </p>
      {types.map((t) => (
        <section key={t} aria-label={TYPES[t] ?? t}>
          <h2>{TYPES[t] ?? t}</h2>
          {data.parts
            .filter((p) => p.type === t)
            .map((p) => (
              <details key={p.id} className="part">
                <summary>
                  <strong>{p.maker}</strong> {p.model}
                  <span className="muted">
                    {" "}
                    {p.mass_g != null ? `${p.mass_g} g` : ""}
                    {p.price_usd != null ? `, ${money(p.price_usd)}` : ""}
                  </span>
                </summary>
                {p.link ? (
                  <p>
                    <a href={p.link} target="_blank" rel="noreferrer">
                      where to buy it
                    </a>
                  </p>
                ) : null}
                <Tree value={p.record} />
              </details>
            ))}
        </section>
      ))}
    </main>
  );
}
