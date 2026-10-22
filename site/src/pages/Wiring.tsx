// The wiring: every board's pins and where each one goes, every wire with its gauge, its cut
// length and what it carries, where each plug's pin positions come from (the maker's drawing or
// my estimate), how hard each route's wires work in each combination, the harness diagrams and
// the schematic, all generated from the one connection list (design/electrical.yaml).
import type { LoadOptions } from "../data/load";
import { COMBINATIONS } from "../data/order";
import type { BoardPins, PinSource, Wire3d, Wires, Wires3d, Wiring as WiringData } from "../data/types";
import { useData } from "../data/useData";

const CARRIES: Record<string, string> = { power: "power", ground: "ground", signal: "a signal", bus: "the CAN bus" };

function WireList({ wires }: { wires: Wire3d[] }) {
  const harnesses = [...new Set(wires.map((w) => w.harness))];
  return (
    <section aria-label="every wire">
      <h2>Every wire</h2>
      <p className="muted">
        {wires.length} wires in all, each cut to its whole run, plug to plug, branches included. The lengths are the
        ones the <a href="#/library/docs/build/wiring">wiring guide</a> cuts to.
      </p>
      {harnesses.map((h) => (
        <div key={h} className="scroll-x">
          <table className="short-columns" aria-label={`the ${h} harness`}>
            <caption>{h}</caption>
            <thead>
              <tr>
                <th scope="col">From</th>
                <th scope="col">To</th>
                <th scope="col">Wire</th>
                <th scope="col">Cut to</th>
                <th scope="col">Carries</th>
              </tr>
            </thead>
            <tbody>
              {wires
                .filter((w) => w.harness === h)
                .map((w) => (
                  <tr key={w.label}>
                    <td>{w.ends[0].pin}</td>
                    <td>{w.ends[1].pin}</td>
                    <td>
                      {w.awg} AWG {w.wire}
                    </td>
                    <td>{Math.round(w.length_mm)} mm</td>
                    <td>{CARRIES[w.role] ?? w.role}</td>
                  </tr>
                ))}
            </tbody>
          </table>
        </div>
      ))}
    </section>
  );
}

function PinSources({ sources }: { sources: PinSource[] }) {
  const estimates = sources.filter((s) => s.estimate).length;
  return (
    <section aria-label="where the pins are">
      <h2>Where each plug's pins are</h2>
      <p className="muted">
        {sources.length - estimates} of the {sources.length} plugs are placed from the maker's drawing, PCB file or
        3D model, and {estimates} are my estimates, each with why. A plug in a socket sits where its socket does.
      </p>
      <div className="scroll-x">
        <table className="short-columns">
          <thead>
            <tr>
              <th scope="col">Plug</th>
              <th scope="col">On</th>
              <th scope="col">From</th>
            </tr>
          </thead>
          <tbody>
            {sources.map((s) => (
              <tr key={s.connector}>
                <td>{s.connector}</td>
                <td>{s.part_id}</td>
                <td>
                  {s.estimate ? "My estimate" : s.url ? (
                    <a href={s.url} target="_blank" rel="noreferrer">
                      The maker's drawing
                    </a>
                  ) : (
                    "The maker"
                  )}
                  {s.note ? `: ${s.note}` : ""}
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </section>
  );
}

function Heating({ wires }: { wires: Wires }) {
  return (
    <section aria-label="how hard the wires work">
      <h2>How hard each route's wires work</h2>
      <p className="muted">
        The hardest-working wire on each route, as a share of the heat it can take, in the worst case each combination
        flies (a burst of full throttle, or a hover where that's worse). Under 100% is inside its limit.
      </p>
      <div className="scroll-x">
        <table className="short-columns">
          <thead>
            <tr>
              <th scope="col">Route</th>
              {COMBINATIONS.map((c) => (
                <th key={c} scope="col">
                  {c}
                </th>
              ))}
            </tr>
          </thead>
          <tbody>
            {wires.routes.map((r) => (
              <tr key={r.name}>
                <td>{r.name}</td>
                {COMBINATIONS.map((c) => {
                  const cases = r.heating_share[c];
                  const share = cases ? Math.max(...Object.values(cases)) : null;
                  return <td key={c}>{share == null ? "" : `${(share * 100).toFixed(0)}%`}</td>;
                })}
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </section>
  );
}

export function wiringLink(board: string): string {
  return `#/wiring/${encodeURIComponent(board)}`;
}

// the boards a 3D piece is, by its catalog part
export function boardsOf(wiring: WiringData | null | undefined, part: string | null): string[] {
  if (!wiring || !part) return [];
  return wiring.boards.filter((b) => b.part === part).map((b) => b.name);
}

function PinMap({ board }: { board: BoardPins }) {
  return (
    <section aria-label={`${board.name}'s pins`}>
      <h3>
        {board.name} <span className="status">{board.part}, {board.module}</span>
      </h3>
      <div className="scroll-x">
        <table className="pins">
          <thead>
            <tr>
              <th scope="col">Pin</th>
              <th scope="col">What it is</th>
              <th scope="col">Called</th>
              <th scope="col">Goes to</th>
              <th scope="col">Harness</th>
            </tr>
          </thead>
          <tbody>
            {board.pins.map((p) => (
              <tr key={p.pin}>
                <td>{p.pin}</td>
                <td>{p.role}</td>
                <td>{p.functions}</td>
                <td>{p.to}</td>
                <td>{p.harness}</td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </section>
  );
}

export function Wiring({ board, load }: { board?: string; load?: LoadOptions }) {
  const { data, problem } = useData<WiringData>("wiring.json", load);
  const all = useData<Wires3d>("wires3d.json", load).data;
  const routes = useData<Wires>("wires.json", load).data;
  if (problem) return <p role="alert">{problem}</p>;
  if (!data) return <p>Loading</p>;
  const picked = data.boards.find((b) => b.name === board) ?? data.boards.find((b) => b.name === "fc") ?? data.boards[0];
  return (
    <main>
      <h1>The wiring</h1>
      <p className="purpose">
        Every board, every pin and every wire, generated from one connection list, so the pin maps, the wire list,
        the harness diagrams and the schematic can't disagree with each other. The checks they pass (currents, voltage
        drops, heating, every pin's role) are in the <a href="#/library/docs/reports/electrical/README">electrical
        report</a>, and how to make each harness is in the <a href="#/library/docs/build/wiring">wiring guide</a>.
      </p>
      <section aria-label="pin maps">
        <h2>Pin maps</h2>
        <label>
          Board{" "}
          <select
            aria-label="board"
            value={picked?.name ?? ""}
            onChange={(e) => {
              window.location.hash = wiringLink(e.target.value);
            }}
          >
            {data.boards.map((b) => (
              <option key={b.name} value={b.name}>
                {b.name} ({b.part})
              </option>
            ))}
          </select>
        </label>
        {picked && <PinMap board={picked} />}
      </section>
      {all?.wires && <WireList wires={all.wires} />}
      {all?.connectors && <PinSources sources={all.connectors} />}
      {routes?.routes && <Heating wires={routes} />}
      <section aria-label="the harnesses">
        <h2>The harnesses</h2>
        <div className="stills">
          {data.harnesses.map((h) => (
            <figure key={h.file}>
              <a href={`./data/${h.file}`} target="_blank" rel="noreferrer">
                <img src={`./data/${h.file}`} alt={`the ${h.name} harness`} loading="lazy" className="harness" />
              </a>
              <figcaption>{h.name}</figcaption>
            </figure>
          ))}
        </div>
      </section>
      <section aria-label="the schematic">
        <h2>The schematic</h2>
        <p className="links">
          {data.schematic && (
            <a href={`./data/${data.schematic}`} target="_blank" rel="noreferrer">
              the whole schematic, as a picture
            </a>
          )}
          <a href={data.kicad} target="_blank" rel="noreferrer">
            its KiCad file
          </a>
        </p>
      </section>
    </main>
  );
}
