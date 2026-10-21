// The wiring: every board's pins and where each one goes, the harness diagrams and the
// schematic, all generated from the one connection list (design/electrical.yaml).
import type { LoadOptions } from "../data/load";
import type { BoardPins, Wiring as WiringData } from "../data/types";
import { useData } from "../data/useData";

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
  if (problem) return <p role="alert">{problem}</p>;
  if (!data) return <p>Loading</p>;
  const picked = data.boards.find((b) => b.name === board) ?? data.boards.find((b) => b.name === "fc") ?? data.boards[0];
  return (
    <main>
      <h1>The wiring</h1>
      <p className="purpose">
        Every board, every pin and every wire, generated from one connection list, so the pin maps, the harness
        diagrams and the schematic can't disagree with each other.
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
