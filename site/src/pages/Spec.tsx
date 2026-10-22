// The spec sheet: each combination's numbers exactly as the sizing report words and rounds them
// (toward failing), every check with its target, margin and note, what its weight is made of,
// how the CAD balances it, and the pack they all share. The parts themselves are on Parts.
import { Fragment, useState } from "react";

import type { LoadOptions } from "../data/load";
import { MODULE_NAMES } from "../data/order";
import type { Combination, MassLine, SpecSheet } from "../data/types";
import { useData } from "../data/useData";

const GROUPS: Record<string, string> = {
  base: "Base",
  V: `V, ${MODULE_NAMES.V.toLowerCase()}`,
  P: `P, ${MODULE_NAMES.P.toLowerCase()}`,
  C: `C, ${MODULE_NAMES.C.toLowerCase()}`,
  payload: "Payload",
  margin: "Growth margin",
};

function Numbers({ c }: { c: Combination }) {
  return (
    <dl className="numbers" aria-label={`${c.name} numbers`}>
      {c.numbers.map(([k, v]) => (
        <div key={k}>
          <dt>{k}</dt>
          <dd>{v}</dd>
        </div>
      ))}
    </dl>
  );
}

function Checks({ c }: { c: Combination }) {
  const notes = c.checks.filter((k) => k.note);
  return (
    <section aria-label={`${c.name} checks`}>
      <h3>The checks</h3>
      <table className="short-columns">
        <thead>
          <tr>
            <th scope="col">Check</th>
            <th scope="col">Published / pessimistic</th>
            <th scope="col">Target</th>
            <th scope="col">Margin</th>
            <th scope="col">Verdict</th>
          </tr>
        </thead>
        <tbody>
          {c.checks.map((k) => (
            <tr key={k.name}>
              <td>{k.name}</td>
              <td>
                {k.shown}
                {k.shown_pessimistic && k.shown_pessimistic !== k.shown ? ` / ${k.shown_pessimistic}` : ""}
              </td>
              <td>{k.shown_limit ?? "none"}</td>
              <td>{k.shown_margin ?? ""}</td>
              <td>
                <span className={`verdict ${k.verdict}`}>{k.verdict}</span>
              </td>
            </tr>
          ))}
        </tbody>
      </table>
      {notes.length > 0 && (
        <ul className="notes">
          {notes.map((k) => (
            <li key={k.name}>
              <strong>{k.name}:</strong> {k.note}
            </li>
          ))}
        </ul>
      )}
    </section>
  );
}

function Weight({ c }: { c: Combination }) {
  const groups: [string, MassLine[]][] = [];
  for (const line of c.mass_lines) {
    const found = groups.find(([g]) => g === line.group);
    if (found) found[1].push(line);
    else groups.push([line.group, [line]]);
  }
  return (
    <section aria-label={`${c.name} weight`}>
      <h3>What it weighs</h3>
      <p className="muted">The sizing model's weight, line by line: the catalog's masses, the printed parts' and the wiring's as the CAD weighs them, and the growth margin kept for what isn't designed yet.</p>
      <table className="short-columns">
        <tbody>
          {groups.map(([group, lines]) => (
            <Fragment key={group}>
              <tr className="group-row">
                <th scope="rowgroup" colSpan={2}>
                  {GROUPS[group] ?? group}
                </th>
              </tr>
              {lines.map((line) => (
                <tr key={`${group}-${line.name}`}>
                  <td>{line.name}</td>
                  <td>{line.grams.toFixed(1)} g</td>
                </tr>
              ))}
              {groups.length > 1 && (
                <tr className="sum-row">
                  <td>{GROUPS[group] ?? group}, in all</td>
                  <td>{lines.reduce((s, l) => s + l.grams, 0).toFixed(1)} g</td>
                </tr>
              )}
            </Fragment>
          ))}
          <tr className="total-row">
            <td>{c.name}, in all</td>
            <td>{c.mass_g.toFixed(1)} g</td>
          </tr>
        </tbody>
      </table>
    </section>
  );
}

function Balance({ c }: { c: Combination }) {
  const b = c.balance;
  if (!b) return null;
  const [x, y, z] = b.center_of_gravity_mm;
  const inertia = b.inertia_kg_m2.map((row, k) => row[k] * 1000);
  return (
    <section aria-label={`${c.name} balance`}>
      <h3>How it balances, in the CAD</h3>
      <dl className="numbers">
        <div>
          <dt>Pack slid to</dt>
          <dd>x = {b.trim_x_mm.toFixed(0)} mm</dd>
        </div>
        <div>
          <dt>Center of gravity</dt>
          <dd>
            {x.toFixed(1)}, {y.toFixed(1)}, {z.toFixed(1)} mm (forward, left, up)
          </dd>
        </div>
        <div>
          <dt>Busiest motor</dt>
          <dd>{(b.busiest_motor_extra * 100).toFixed(1)}% harder than the others</dd>
        </div>
        <div>
          <dt>Inertia</dt>
          <dd>
            {inertia.map((v) => v.toFixed(2)).join(", ")} g m² (roll, pitch, yaw)
          </dd>
        </div>
        <div>
          <dt>CAD checks</dt>
          <dd>
            <span className={`verdict ${b.passed ? "pass" : "fail"}`}>{b.passed ? "pass" : "fail"}</span>
          </dd>
        </div>
      </dl>
    </section>
  );
}

export function Spec({ load }: { load?: LoadOptions }) {
  const { data, problem } = useData<SpecSheet>("spec.json", load);
  const [picked, setPicked] = useState<string | null>(null);
  if (problem) return <p role="alert">{problem}</p>;
  if (!data) return <p>Loading</p>;
  const c = data.combinations.find((x) => x.name === picked) ?? data.combinations[0];
  const t = data.targets;
  return (
    <main>
      <h1>The spec sheet</h1>
      <p className="purpose">
        Each combination's numbers, worded and rounded as the{" "}
        <a href="#/library/docs/reports/sizing/README">sizing report</a> has them: rounding always goes toward failing, so
        a value that has to stay high rounds down. The sizing case is {data.sizing_case}, with a{" "}
        {((t.reserve_fraction ?? 0) * 100).toFixed(0)}% reserve, a {t.cruise_speed_ms} m/s cruise and at least{" "}
        {t.min_thrust_to_weight}:1 thrust to weight. The weights and balance come from the{" "}
        <a href="#/library/docs/reports/cad/README">CAD report</a>, the parts with their prices from{" "}
        <a href="#/parts">Parts</a>, and how each number is worked out from <a href="#/math">The math</a>.
      </p>
      <div role="tablist" aria-label="combination">
        {data.combinations.map((x) => (
          <button key={x.name} type="button" role="tab" aria-selected={x.name === c.name} onClick={() => setPicked(x.name)}>
            {x.name}
          </button>
        ))}
      </div>
      <h2>
        {c.name} {c.modules.length ? `(${c.modules.join(", ")})` : "(no modules)"}, {c.required ? "required" : "optional"}
        : <span className={`verdict ${c.verdict}`}>{c.verdict}</span>
      </h2>
      <Numbers c={c} />
      <Checks c={c} />
      <Weight c={c} />
      <Balance c={c} />
      {data.pack && (
        <section aria-label="the pack">
          <h2>The pack, in every combination</h2>
          <dl className="numbers">
            <div>
              <dt>Cells</dt>
              <dd>
                {data.pack.series}S{data.pack.parallel}P {data.pack.cell}
              </dd>
            </div>
            <div>
              <dt>Capacity</dt>
              <dd>{data.pack.capacity_mah.toFixed(0)} mAh</dd>
            </div>
            <div>
              <dt>Resistance</dt>
              <dd>{data.pack.resistance_mohm.toFixed(1)} mΩ, the whole pack</dd>
            </div>
            <div>
              <dt>Weight</dt>
              <dd>{data.pack.mass_g.toFixed(0)} g, the cells and what holds them together</dd>
            </div>
          </dl>
        </section>
      )}
    </main>
  );
}
