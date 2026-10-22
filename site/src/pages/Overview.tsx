// The overview: what the drone is, its three modules, the eight combinations they make with each
// one's weight, hover and verdict, where every step stands, and how to read the rest of these
// docs. The first page of the manual.
import type { LoadOptions } from "../data/load";
import { MODULE_NAMES } from "../data/order";
import type { SpecSheet, Steps } from "../data/types";
import { useData } from "../data/useData";
import { MENU_GROUPS } from "../stage/modes";

// what each page of the docs holds, in a line
const ABOUT: Record<string, string> = {
  overview: "This page.",
  spec: "Each combination's numbers as the reports have them: the checks, what it weighs, how it balances, the pack.",
  parts: "Everything on the drone, with prices, masses, sources and fallbacks, and the parts compared and not picked.",
  wiring: "Every board's pins, every wire with its gauge and cut length, the harnesses and the schematic.",
  flights: "Every scenario flown on PX4 and on my firmware, what each tests, and why the misses missed.",
  tunnel: "The air from six ways and in the hover, recorded moving, with FluidX3D's forces and how it was run.",
  unproven: "What the simulations can't settle, each with how it gets measured on the real thing.",
  steps: "The plan, step by step, with where each stands and its key numbers.",
  build: "What each combination costs, and the guides to build one: assembly, wiring, firmware, tests, the rules.",
  library: "Every doc in the repo: the decisions, the reports, the logs, the specs and the plans.",
  data: "Each report's own data file, whole, to open a branch at a time.",
  math: "How the numbers are worked out, in the code's own words.",
};

const MODULES: [string, string][] = [
  ["V", "A Raspberry Pi 5 companion computer, a camera, the GPS and a HaLow link to the laptop."],
  ["P", "A Fruity Chutes Harrier launcher with its canopy, fired by the flight controller or the safety monitor."],
  ["C", "Claws for grabbing a payload. A placeholder until I settle on a design."],
];

export function Overview({ load }: { load?: LoadOptions }) {
  const spec = useData<SpecSheet>("spec.json", load);
  const steps = useData<Steps>("steps.json", load);
  const problem = spec.problem ?? steps.problem;
  if (problem) return <p role="alert">{problem}</p>;
  if (!spec.data || !steps.data) return <p>Loading</p>;
  return (
    <main>
      <h1>Extra 15pc Gum</h1>
      <p className="purpose">
        A long-range quadcopter with my own flight firmware. Since 2026-10-17 it's a research project: every real part
        modeled, connected and simulated, down to the wiring, complete enough that I could build it one day. Nothing
        gets bought by default. These pages are its documentation.
      </p>
      <section aria-label="the modules">
        <h2>Base and three modules</h2>
        <p>
          Base is the drone that flies: the 10-inch frame, four motors, a 6S2P pack, the flight controller, the
          receiver, the lidar, Remote ID, and a safety monitor of its own that can cut the motors. Three modules plug
          into it, each through the same slot.
        </p>
        <dl className="numbers">
          {MODULES.map(([m, what]) => (
            <div key={m}>
              <dt>
                {m}: {MODULE_NAMES[m].toLowerCase()}
              </dt>
              <dd>{what}</dd>
            </div>
          ))}
        </dl>
      </section>
      <section aria-label="the combinations">
        <h2>The eight combinations</h2>
        <div className="scroll-x">
          <table className="short-columns">
            <thead>
              <tr>
                <th scope="col">Combination</th>
                <th scope="col">Modules</th>
                <th scope="col">Weight</th>
                <th scope="col">Hover, published / pessimistic</th>
                <th scope="col">Verdict</th>
              </tr>
            </thead>
            <tbody>
              {spec.data.combinations.map((c) => {
                const hover = c.checks.find((k) => k.name === "Hover time");
                return (
                  <tr key={c.name}>
                    <td>
                      {c.name}
                      {c.required ? "" : <span className="muted">, optional</span>}
                    </td>
                    <td>{c.modules.length ? c.modules.join(" + ") : "none"}</td>
                    <td>{c.mass_g.toFixed(0)} g</td>
                    <td>{hover ? `${hover.shown} / ${hover.shown_pessimistic ?? ""}` : ""}</td>
                    <td>
                      <span className={`verdict ${c.verdict}`}>{c.verdict}</span>
                    </td>
                  </tr>
                );
              })}
            </tbody>
          </table>
        </div>
        <p className="muted">
          The sizing model's weights, with the growth margin. Every check, in full, is on the <a href="#/spec">spec
          sheet</a>.
        </p>
      </section>
      <section aria-label="where it stands">
        <h2>Where each step stands</h2>
        <ul className="steps">
          {steps.data.steps.map((s) => (
            <li key={s.id}>
              <a href={`#/steps/${s.id}`}>
                {s.number ? `${s.number}. ` : ""}
                {s.name}
              </a>{" "}
              <span className="status">{s.status}</span>
            </li>
          ))}
        </ul>
      </section>
      <section aria-label="these docs">
        <h2>How to read these docs</h2>
        {MENU_GROUPS.map((g) => (
          <section key={g.name} aria-label={g.name}>
            <h3>{g.name}</h3>
            <dl className="numbers">
              {g.pages
                .filter((p) => p.route !== "overview")
                .map((p) => (
                  <div key={p.route}>
                    <dt>
                      <a href={`#/${p.route}`}>{p.name}</a>
                    </dt>
                    <dd>{ABOUT[p.route]}</dd>
                  </div>
                ))}
            </dl>
          </section>
        ))}
        <p className="muted">
          The 3D drone behind these pages shows the same things live: <a href="#/">Inside it</a>, every wire pin to
          pin, and Fly it, every run and the wind tunnel as animations.
        </p>
      </section>
    </main>
  );
}
