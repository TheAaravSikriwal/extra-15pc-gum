// What the sims can't prove: the project's own list, each with the first thing to measure once
// it's built, and each report's. Linked from the home page, so it's never more than a click away.
import type { LoadOptions } from "../data/load";
import type { Unproven as UnprovenData } from "../data/types";
import { useData } from "../data/useData";

export function countUnproven(data: UnprovenData): number {
  return data.groups.reduce((n, g) => n + g.items.length, 0);
}

export function Unproven({ load }: { load?: LoadOptions }) {
  const { data, problem } = useData<UnprovenData>("unproven.json", load);
  if (problem) return <p role="alert">{problem}</p>;
  if (!data) return <p>Loading</p>;
  return (
    <main>
      <h1>What the sims can't prove</h1>
      <p className="purpose">
        Everything here is simulated, and a simulation only knows what it's told. These are the things it can't settle,
        and for the drone as a whole, the first thing to measure once one is built.
      </p>
      {data.groups.map((g) => (
        <section key={g.name} aria-label={g.name}>
          <h2>{g.name}</h2>
          {g.items.some((i) => i.measure) ? (
            <table className="unproven">
              <thead>
                <tr>
                  <th scope="col">What the sim can't prove</th>
                  <th scope="col">First thing to measure</th>
                </tr>
              </thead>
              <tbody>
                {g.items.map((i) => (
                  <tr key={i.what}>
                    <td>{i.what}</td>
                    <td>{i.measure}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          ) : (
            <ul>
              {g.items.map((i) => (
                <li key={i.what}>{i.what}</li>
              ))}
            </ul>
          )}
          <p className="links">
            <a href={g.url} target="_blank" rel="noreferrer">
              where it's written
            </a>
          </p>
        </section>
      ))}
    </main>
  );
}
