// Build it: what each combination costs, the guides to build one from the docs alone (the parts
// list, assembly, wiring, firmware, the tests, the rules), and what's still open. The parts
// themselves, line by line, are on Parts.
import type { LoadOptions } from "../data/load";
import { byCombination } from "../data/order";
import type { Build as BuildData } from "../data/types";
import { useData } from "../data/useData";
import { money } from "./Parts";

export function Build({ load }: { load?: LoadOptions }) {
  const { data, problem } = useData<BuildData>("build.json", load);
  if (problem) return <p role="alert">{problem}</p>;
  if (!data) return <p>Loading</p>;
  const once = data.totals.find((t) => t.setup === "once");
  return (
    <main>
      <h1>Build it</h1>
      <p className="purpose">
        Everything to build one from the docs alone. Nothing has been built yet: this is the plan for the first one,
        written by <code>pcs14 package</code> on {data.generated} from the catalog, the build, the connection list and the
        CAD. Every part, with its price, its link and what to buy if it's gone, is on <a href="#/parts">Parts</a>.
      </p>
      <section aria-label="What it costs">
        <h2>What it costs</h2>
        <table className="short-columns">
          <thead>
            <tr>
              <th scope="col">Combination</th>
              <th scope="col">Parts, wire and plugs</th>
              <th scope="col">Not priced yet</th>
              <th scope="col">Printed</th>
            </tr>
          </thead>
          <tbody>
            {byCombination(
              data.totals.filter((t) => t.setup !== "once"),
              (t) => t.setup,
            ).map((t) => (
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
            Bought once, whatever's fitted (the transmitter, the charger, tools and spares): {money(once.usd)}, with{" "}
            {once.unpriced} not priced yet.
          </p>
        ) : null}
        <p className="muted">Prices are what the shops showed on the day each part was checked, and they drift.</p>
      </section>
      <section aria-label="the guides">
        <h2>The guides</h2>
        <dl className="numbers">
          {data.guides.map((g) => (
            <div key={g.name}>
              <dt>
                <a href={g.url}>{g.name}</a>
              </dt>
              <dd>{g.about}</dd>
            </div>
          ))}
        </dl>
      </section>
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
