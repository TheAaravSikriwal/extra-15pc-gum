// Build it: the build package's parts list and totals, from build.json, with links to the guides
// (assembly, wiring, firmware, tests, the legal checklist) where they're written in the repo.
import type { LoadOptions } from "../data/load";
import type { Build as BuildData, BuildLine } from "../data/types";
import { useData } from "../data/useData";

const MODULES: [string, string][] = [
  ["base", "Base"],
  ["V", "V: vision and nav"],
  ["P", "P: the parachute"],
  ["C", "C: the claws"],
  ["once", "Bought once"],
];
const SHOWN = new Set(["bought", "wire", "plug", "ground", "supplies", "tools", "spares"]);

export function money(usd: number | null | undefined): string {
  return usd == null ? "?" : `$${usd.toLocaleString("en-US", { minimumFractionDigits: 2, maximumFractionDigits: 2 })}`;
}

function amount(line: BuildLine): string {
  return `${line.qty}${line.unit ? ` ${line.unit}` : ""}`;
}

export function Build({ load }: { load?: LoadOptions }) {
  const { data, problem } = useData<BuildData>("build.json", load);
  if (problem) return <p role="alert">{problem}</p>;
  if (!data) return <p>Loading</p>;
  const once = data.totals.find((t) => t.setup === "once");
  return (
    <main>
      <h1>Build it</h1>
      <p className="purpose">
        Everything to build one from the docs alone: what to buy and print, how to wire it and put it together, the
        firmware, the tests before the props go on, and the rules. Nothing has been built yet; this is the plan for the
        first one. Prices are what the shops showed when each part was checked, and a ? hasn't been checked.
      </p>
      <p className="links">
        {data.guides.map((g) => (
          <a key={g.name} href={g.url} target="_blank" rel="noreferrer">
            {g.name}
          </a>
        ))}
      </p>
      <section aria-label="What it costs">
        <h2>What it costs</h2>
        <table>
          <thead>
            <tr>
              <th scope="col">Combination</th>
              <th scope="col">Parts, wire and plugs</th>
              <th scope="col">Not priced yet</th>
              <th scope="col">Printed</th>
            </tr>
          </thead>
          <tbody>
            {data.totals
              .filter((t) => t.setup !== "once")
              .map((t) => (
                <tr key={t.setup}>
                  <td>{t.setup}</td>
                  <td>{money(t.usd)}</td>
                  <td>{t.unpriced}</td>
                  <td>
                    {t.printed} parts, {Math.round(t.printed_g)} g
                  </td>
                </tr>
              ))}
          </tbody>
        </table>
        {once ? (
          <p>
            Bought once, whatever's fitted: {money(once.usd)}, with {once.unpriced} not priced yet.
          </p>
        ) : null}
      </section>
      {MODULES.map(([module, name]) => {
        const lines = data.lines.filter((x) => x.module === module && SHOWN.has(x.group));
        if (!lines.length) return null;
        return (
          <section key={module} aria-label={name}>
            <h2>{name}</h2>
            <table className="parts">
              <thead>
                <tr>
                  <th scope="col">Part</th>
                  <th scope="col">How many</th>
                  <th scope="col">Each</th>
                  <th scope="col">If it's gone</th>
                </tr>
              </thead>
              <tbody>
                {lines.map((x) => (
                  <tr key={`${x.group}-${x.name}`}>
                    <td>
                      {x.link ? (
                        <a href={x.link} target="_blank" rel="noreferrer">
                          {x.name}
                        </a>
                      ) : (
                        x.name
                      )}
                      <br />
                      <span className="muted">{x.maker}</span>
                    </td>
                    <td>{amount(x)}</td>
                    <td>{money(x.price_each_usd)}</td>
                    <td>{x.fallback.replace(/\[([^\]]+)\]\([^)]+\)/g, "$1")}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          </section>
        );
      })}
      <section aria-label="Still open">
        <h2>Still open</h2>
        <ul>
          {data.open.map((o) => (
            <li key={o}>{o}</li>
          ))}
        </ul>
      </section>
    </main>
  );
}
