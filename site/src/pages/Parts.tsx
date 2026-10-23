// Parts: everything that goes on the drone, from the build package, by module and kind (bought,
// wire, plugs, screws, printed), each line with its price on the day it was checked, its mass, a
// note where it has one, what to buy if it's gone, and its catalog entry with every field the
// design reads. Then the rest of the catalog, the parts compared and not picked. This is the one
// home for the parts: the spec sheet and Build it point here.
import { type ReactNode } from "react";

import type { LoadOptions } from "../data/load";
import { MODULE_NAMES } from "../data/order";
import type { CatalogPart, PartsLine, PartsList } from "../data/types";
import { useData } from "../data/useData";
import { Tree } from "./Tree";

const MODULES: [string, string][] = [
  ["base", "Base"],
  ["V", `V: ${MODULE_NAMES.V.toLowerCase()}`],
  ["P", `P: ${MODULE_NAMES.P.toLowerCase()}`],
  ["C", `C: ${MODULE_NAMES.C.toLowerCase()}`],
  ["once", "Bought once, whatever's fitted"],
];

const GROUPS: [string, string][] = [
  ["bought", "Bought"],
  ["wire", "Wire"],
  ["plug", "Plugs"],
  ["hardware", "Screws, nuts and the rest"],
  ["printed", "Printed"],
  ["ground", "On the ground"],
  ["supplies", "Supplies"],
  ["tools", "Tools"],
  ["spares", "Spares"],
];

const TYPES: [string, string][] = [
  ["cell", "Cells"],
  ["motor", "Motors"],
  ["prop", "Props"],
  ["esc", "ESCs"],
  ["frame", "Frames"],
  ["wire", "Wire"],
  ["component", "Boards, sensors and the rest"],
];

export function money(usd: number | null | undefined): string {
  return usd == null ? "not priced" : `$${usd.toLocaleString("en-US", { minimumFractionDigits: 2, maximumFractionDigits: 2 })}`;
}

// Markdown links in a line of text, as links
export function linked(text: string): ReactNode[] {
  const out: ReactNode[] = [];
  const pattern = /\[([^\]]+)\]\(([^)]+)\)/g;
  let last = 0;
  for (let m = pattern.exec(text); m; m = pattern.exec(text)) {
    out.push(text.slice(last, m.index));
    out.push(
      <a key={m.index} href={m[2]} target="_blank" rel="noreferrer">
        {m[1]}
      </a>,
    );
    last = m.index + m[0].length;
  }
  out.push(text.slice(last));
  return out;
}

// what the build package prices: the bought parts, the wire and the plugs, not the screws or what's printed
const UNPRICED_GROUPS = new Set(["printed", "hardware"]);

export function totalOf(lines: PartsLine[]): { usd: number; unpriced: number } {
  const priced = lines.filter((x) => !UNPRICED_GROUPS.has(x.group));
  return {
    usd: priced.reduce((sum, x) => sum + (x.total_usd ?? 0), 0),
    unpriced: priced.filter((x) => x.total_usd == null).length,
  };
}

function notYet(n: number): string {
  return n ? `, and ${n} ${n === 1 ? "line" : "lines"} not priced yet` : "";
}

function amount(line: PartsLine): string {
  const qty = Number.isInteger(line.qty) ? String(line.qty) : line.qty.toFixed(2);
  return `${qty}${line.unit ? ` ${line.unit}` : ""}`;
}

function Line({ line, record }: { line: PartsLine; record?: CatalogPart }) {
  const what = ["Printed", "Any", "Various"].includes(line.maker) ? line.model : `${line.maker} ${line.model}`;
  return (
    <tr>
      <td>
        <details className="part">
          <summary>{line.name}</summary>
          <dl>
            <dt>What</dt>
            <dd>{what}</dd>
            {line.link && (
              <>
                <dt>Where</dt>
                <dd>
                  <a href={line.link} target="_blank" rel="noreferrer">
                    the shop's page
                  </a>
                </dd>
              </>
            )}
            {line.note && (
              <>
                <dt>Note</dt>
                <dd>{line.note}</dd>
              </>
            )}
            {line.fallback && (
              <>
                <dt>If it's gone</dt>
                <dd>{linked(line.fallback)}</dd>
              </>
            )}
          </dl>
          {record && (
            <details className="record">
              <summary>Its catalog entry, every field</summary>
              <Tree value={record.record} />
            </details>
          )}
        </details>
      </td>
      <td>{amount(line)}</td>
      <td>{line.mass_g != null ? `${line.mass_g} g` : ""}</td>
      <td>
        {money(line.price_each_usd)}
        {line.unit && line.price_each_usd != null ? ` a ${line.unit}` : ""}
      </td>
      <td>{line.total_usd != null ? money(line.total_usd) : ""}</td>
      <td>{line.checked ?? ""}</td>
    </tr>
  );
}

export function Parts({ load }: { load?: LoadOptions }) {
  const { data, problem } = useData<PartsList>("parts-list.json", load);
  if (problem) return <p role="alert">{problem}</p>;
  if (!data) return <p>Loading</p>;
  const records = new Map(data.used.map((p) => [p.id, p]));
  const drone = totalOf(data.lines.filter((x) => x.module !== "once"));
  const once = totalOf(data.lines.filter((x) => x.module === "once"));
  return (
    <main>
      <h1>Parts</h1>
      <p className="purpose">
        Everything that goes on the drone, by module: what to buy, the wire, the plugs, the screws and what to print,{" "}
        {data.lines.length} lines in all. Open a line for its note, what to buy if it's gone, and its catalog entry with
        every field the design reads and where each number came from. Prices are what the shop showed on the day in
        the last column. What each combination costs is on <a href="#/build">Build it</a>, and what the parts weigh in
        each combination on the <a href="#/spec">spec sheet</a>.
      </p>
      <p className="total">
        The whole drone, every module on: <strong>{money(drone.usd)}</strong> in parts, wire and plugs, plus{" "}
        {money(once.usd)} bought once, so <strong>{money(drone.usd + once.usd)}</strong> in all
        {notYet(drone.unpriced + once.unpriced)}. The screws and the printed parts aren't in it: they're cheap, and the
        printed ones are filament. Each combination's total is on <a href="#/build">Build it</a>.
      </p>
      {MODULES.map(([module, name]) => {
        const lines = data.lines.filter((x) => x.module === module);
        if (!lines.length) return null;
        return (
          <section key={module} aria-label={name}>
            <h2>{name}</h2>
            <p className="total">
              In all: <strong>{money(totalOf(lines).usd)}</strong>
              {notYet(totalOf(lines).unpriced)}.
            </p>
            {GROUPS.map(([group, label]) => {
              const here = lines.filter((x) => x.group === group);
              if (!here.length) return null;
              return (
                <div key={group} className="scroll-x">
                  <table className="parts short-columns" aria-label={`${name}: ${label}`}>
                    <caption>{label}</caption>
                    <thead>
                      <tr>
                        <th scope="col">Part</th>
                        <th scope="col">How many</th>
                        <th scope="col">Each weighs</th>
                        <th scope="col">Each costs</th>
                        <th scope="col">In all</th>
                        <th scope="col">Checked</th>
                      </tr>
                    </thead>
                    <tbody>
                      {here.map((x) => (
                        <Line key={`${x.group}-${x.name}`} line={x} record={x.catalog_id ? records.get(x.catalog_id) : undefined} />
                      ))}
                    </tbody>
                  </table>
                </div>
              );
            })}
          </section>
        );
      })}
      <section aria-label="not on the drone">
        <h2>In the catalog, not on the drone</h2>
        <p className="muted">
          The parts I compared and didn't pick, or that the design moved past, each with every field the catalog holds.
        </p>
        {TYPES.map(([type, label]) => {
          const parts = data.alternatives.filter((p) => p.type === type);
          if (!parts.length) return null;
          return (
            <section key={type} aria-label={label}>
              <h3>{label}</h3>
              {parts.map((p) => (
                <details key={p.id} className="part">
                  <summary>
                    <strong>{p.maker}</strong> {p.model}
                    <span className="muted">
                      {" "}
                      {p.mass_g != null ? `${p.mass_g} g` : ""}
                      {p.price_usd != null ? `, ${money(p.price_usd)}` : ""}
                    </span>
                  </summary>
                  <Tree value={p.record} />
                </details>
              ))}
            </section>
          );
        })}
      </section>
    </main>
  );
}
