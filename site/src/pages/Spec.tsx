// The live spec sheet: each combination's weights, flight times, thrust and speeds, from the
// sizing report and the CAD's own weighing, and the parts that make it.
import { useState } from "react";

import { Bars } from "../charts/Bars";
import type { LoadOptions } from "../data/load";
import type { Combination, SpecSheet } from "../data/types";
import { useData } from "../data/useData";

function check(c: Combination, name: string) {
  return c.checks.find((k) => k.name.startsWith(name));
}

function Numbers({ c }: { c: Combination }) {
  const hover = check(c, "Hover time");
  const cruise = check(c, "Cruise time");
  const thrust = check(c, "Thrust-to-weight");
  const rows: [string, string][] = [
    ["Weight, sizing model", `${c.mass_g.toFixed(0)} g (with ${c.growth_margin_g.toFixed(0)} g of margin)`],
    ["Weight, CAD", c.cad_mass_g ? `${c.cad_mass_g.toFixed(0)} g` : "not weighed yet"],
    ["Hover", hover ? `${hover.nominal.toFixed(1)} min (${hover.pessimistic?.toFixed(1)} pessimistic)` : ""],
    ["Cruise", cruise ? `${cruise.nominal.toFixed(1)} min (${cruise.pessimistic?.toFixed(1)} pessimistic)` : ""],
    ["Thrust-to-weight at the reserve", thrust ? `${thrust.nominal.toFixed(2)}:1` : ""],
    ["Top speed, full pack", `${(c.top_speed_kmh.full ?? 0).toFixed(0)} km/h`],
    ["Farthest per charge", `${c.least_power_speed_ms.toFixed(1)} m/s for ${c.least_power_minutes.toFixed(1)} min`],
  ];
  return (
    <dl className="numbers" aria-label={`${c.name} numbers`}>
      {rows.map(([k, v]) => (
        <div key={k}>
          <dt>{k}</dt>
          <dd>{v}</dd>
        </div>
      ))}
    </dl>
  );
}

export function Spec({ load }: { load?: LoadOptions }) {
  const { data, problem } = useData<SpecSheet>("spec.json", load);
  const [picked, setPicked] = useState<string | null>(null);
  if (problem) return <p role="alert">{problem}</p>;
  if (!data) return <p>Loading</p>;
  const c = data.combinations.find((x) => x.name === picked) ?? data.combinations[0];
  return (
    <main>
      <h1>The spec sheet</h1>
      <div role="tablist" aria-label="combination">
        {data.combinations.map((x) => (
          <button
            key={x.name}
            type="button"
            role="tab"
            aria-selected={x.name === c.name}
            onClick={() => setPicked(x.name)}
          >
            {x.name}
          </button>
        ))}
      </div>
      <h2>
        {c.name} {c.modules.length ? `(${c.modules.join(", ")})` : "(no modules)"}:{" "}
        <span className={`verdict ${c.verdict}`}>{c.verdict}</span>
      </h2>
      <Numbers c={c} />
      <Bars
        title={`${c.name} checks`}
        bars={c.checks
          .filter((k) => k.limit != null)
          .map((k) => ({
            name: k.name,
            value: k.nominal,
            limit: k.limit as number,
            unit: k.unit,
            higherIsBetter: k.higher_is_better,
            pessimistic: k.pessimistic,
            verdict: k.verdict,
          }))}
      />
      <h2>The parts</h2>
      <table className="parts short-columns">
        <thead>
          <tr>
            <th scope="col">Part</th>
            <th scope="col">Module</th>
            <th scope="col">Count</th>
            <th scope="col">Each</th>
          </tr>
        </thead>
        <tbody>
          {data.parts.map((p) => (
            <tr key={`${p.module ?? "base"}-${p.id}`}>
              <td>{["Printed", "Various"].includes(p.maker) ? p.model : `${p.maker} ${p.model}`}</td>
              <td>{p.module ?? "base"}</td>
              <td>{p.count}</td>
              <td>{p.mass_g.toFixed(1)} g</td>
            </tr>
          ))}
        </tbody>
      </table>
    </main>
  );
}
