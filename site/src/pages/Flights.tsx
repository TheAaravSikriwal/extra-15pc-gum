// Flights: every scenario from steps 4 to 7, flown in Gazebo and graded the same way. Each
// firmware's runs as a matrix per step, the combinations in their one order; what each scenario
// tests, with a drawing of its run; and why each miss missed. Every flown cell opens its run.
import { Matrix } from "../charts/Matrix";
import type { LoadOptions } from "../data/load";
import { COMBINATIONS } from "../data/order";
import type { Flights as FlightsData, Glyph, Run } from "../data/types";
import { useData } from "../data/useData";
import { cellFor } from "../flights/playback";

export function runLink(setup: string, scenario: string): string {
  return `#/flights/${encodeURIComponent(setup)}/${encodeURIComponent(scenario)}`;
}

const NAMES: Record<string, string> = { px4: "PX4 v1.17.0", mine: "My firmware" };
const STEPS: [number, string][] = [
  [4, "Flight (step 4)"],
  [6, "Modules (step 6)"],
  [7, "Smart features (step 7)"],
];

// a run's shape, small: its path from above, or its height over time
export function RunGlyph({ glyph }: { glyph?: Glyph | null }) {
  const points = (glyph?.points ?? [])
    .map(([x, y]) => (glyph?.kind === "plan" ? [6 + x * 14, 15 - y * 14] : [1 + x * 24, 15 - y * 14]))
    .map(([x, y]) => `${x.toFixed(1)},${y.toFixed(1)}`)
    .join(" ");
  return (
    <svg className="glyph" viewBox="0 0 26 16" aria-hidden="true">
      {points && <polyline points={points} />}
    </svg>
  );
}

function flownIn(runs: Run[], scenario: string, firmware: string): string[] {
  const setups = runs.filter((r) => r.scenario === scenario && r.firmware === firmware && r.flown).map((r) => r.setup);
  return COMBINATIONS.filter((c) => setups.includes(c));
}

export function Flights({ load }: { load?: LoadOptions }) {
  const { data, problem } = useData<FlightsData>("flights.json", load);
  if (problem) return <p role="alert">{problem}</p>;
  if (!data) return <p>Loading</p>;
  const about = new Map(data.about.map((a) => [a.name, a]));
  const columns = COMBINATIONS.filter((c) => data.setups.includes(c));
  const stepOf = (s: string) => about.get(s)?.step ?? 4;
  const missed = data.runs.filter((r) => r.flown && !r.passed);
  const px4 = data.runs.filter((r) => r.firmware === "px4").length;
  // the step 4 scenarios that only apply to some combinations, by how many
  const some = new Map<number, string[]>();
  for (const s of data.scenarios.filter((x) => stepOf(x) === 4)) {
    const n = flownIn(data.runs, s, "px4").length;
    if (n > 0 && n < columns.length) some.set(n, [...(some.get(n) ?? []), s]);
  }
  const partly = [...some].sort(([a], [b]) => a - b).map(([n, names]) => `${names.join(" and ")} in ${n}`);
  return (
    <main className="wide">
      <h1>Flights</h1>
      <p className="purpose">
        Every scenario from steps 4 to 7, flown in Gazebo and graded by the same checks. Step 4's twelve were flown by
        PX4 and by my firmware in each combination a scenario applies to: {px4} runs each
        {partly.length ? `, since not every scenario flies in all ${columns.length} (${partly.join("; ")})` : ""}. Steps 6 and 7's
        modules and smart features were flown by mine alone. A blank cell is a combination that doesn't fly that
        scenario. Open any run to watch it, or play it on the 3D drone in <a href="#/fly">Fly it</a>. The full report
        is the <a href="#/library/docs/reports/flight-sim/README">flight sim report</a>.
      </p>
      {["px4", "mine"].map((firmware) => {
        const runs = data.runs.filter((r) => r.firmware === firmware);
        const passed = runs.filter((r) => r.passed).length;
        return (
          <section key={firmware} aria-label={NAMES[firmware]}>
            <h2>
              {NAMES[firmware]}: {passed} of {runs.length} pass
            </h2>
            {STEPS.map(([step, name]) => {
              const rows = data.scenarios.filter((s) => stepOf(s) === step && runs.some((r) => r.scenario === s));
              if (!rows.length) return null;
              const here = runs.filter((r) => rows.includes(r.scenario));
              return (
                <div key={step} className="scroll-x">
                  <h3>
                    {name}: {here.filter((r) => r.passed).length} of {here.length} pass
                  </h3>
                  <Matrix
                    title={`${NAMES[firmware]}, ${name}`}
                    rows={rows}
                    columns={columns}
                    cell={(scenario, setup) =>
                      runs.some((r) => r.scenario === scenario && r.setup === setup) ? cellFor(data, firmware, scenario, setup) : ""
                    }
                    link={(scenario, setup) => runLink(setup, scenario)}
                  />
                </div>
              );
            })}
          </section>
        );
      })}
      <section aria-label="what each scenario tests">
        <h2>What each scenario tests</h2>
        {STEPS.map(([step, name]) => (
          <section key={step} aria-label={name}>
            <h3>{name}</h3>
            <ul className="scenario-list">
              {data.scenarios
                .filter((s) => stepOf(s) === step)
                .map((s) => {
                  const glyph = data.runs.find((r) => r.scenario === s && r.glyph)?.glyph;
                  const px4In = flownIn(data.runs, s, "px4");
                  const mineIn = flownIn(data.runs, s, "mine");
                  return (
                    <li key={s}>
                      <RunGlyph glyph={glyph} />
                      <div>
                        <strong>{s}</strong> {about.get(s)?.what}
                        <span className="muted">
                          {" "}
                          Flown {px4In.length ? `by PX4 in ${px4In.join(", ")}, and ` : ""}by mine in{" "}
                          {mineIn.length ? mineIn.join(", ") : "none yet"}.
                        </span>
                      </div>
                    </li>
                  );
                })}
            </ul>
          </section>
        ))}
      </section>
      <section aria-label="why the misses missed">
        <h2>Why the misses missed</h2>
        <p className="muted">Each failed run's first failed check, as the grader wrote it.</p>
        <div className="scroll-x">
          <table className="short-columns">
            <thead>
              <tr>
                <th scope="col">Firmware</th>
                <th scope="col">Scenario</th>
                <th scope="col">Combination</th>
                <th scope="col">What it missed</th>
              </tr>
            </thead>
            <tbody>
              {missed.map((r) => (
                <tr key={`${r.firmware}-${r.scenario}-${r.setup}`}>
                  <td>{NAMES[r.firmware]}</td>
                  <td>
                    <a href={runLink(r.setup, r.scenario)}>{r.scenario}</a>
                  </td>
                  <td>{r.setup}</td>
                  <td>{r.missed}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </section>
    </main>
  );
}
