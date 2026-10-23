// The wind tunnel: the seven cases in one table (the air from each way and the hover, as the drone
// view names them, each with its tunnel, grid, seconds of air and force), how it was run, and each
// case's frames played in slow motion with its stills beside it. Pictures, not measurements: the
// drag numbers come from OpenFOAM.
import { useEffect, useMemo, useState } from "react";

import type { LoadOptions } from "../data/load";
import type { Tunnel as TunnelData, TunnelCase, TunnelFrame, TunnelStill } from "../data/types";
import { useData } from "../data/useData";
import { Clock, useClockTime } from "../play/clock";
import { Controls } from "../play/Controls";

export const TUNNEL_SPEEDS = [0.005, 0.01, 0.02, 0.05, 0.1];
const SLOW = 0.02;

const VIEW_NAMES: Record<string, string> = {
  "side-speed": "the air's speed, face on",
  "quarter-vortices": "the vortices, from three quarters",
};

export function viewName(view: string): string {
  return VIEW_NAMES[view] ?? view.replace(/-/g, " ");
}

export function formatMs(t: number): string {
  return `${Math.round(t * 1000)} ms`;
}

// the last frame at or before `t` (the first until it comes)
export function frameAt(frames: TunnelFrame[], t: number): number {
  let found = 0;
  frames.forEach((f, k) => {
    if (f.t_s <= t) found = k;
  });
  return found;
}

export function CaseView({ run, stills = [], now }: { run: TunnelCase; stills?: TunnelStill[]; now?: () => number }) {
  const views = useMemo(() => Array.from(new Set(run.frames.flatMap((f) => Object.keys(f.files)))), [run]);
  const [view, setView] = useState(views[0]);
  const clock = useMemo(() => {
    const made = new Clock({ duration: run.frames[run.frames.length - 1]?.t_s ?? 0, now });
    made.setSpeed(SLOW);
    return made;
  }, [run, now]);
  const time = useClockTime(clock);
  const frame = run.frames[frameAt(run.frames, time)];
  useEffect(() => {
    // fetched ahead, so the frames play without a gap
    for (const f of run.frames) if (f.files[view]) new Image().src = `./data/${f.files[view]}`;
  }, [run, view]);
  const file = frame?.files[view];
  return (
    <section aria-label={run.label} className="tunnel-case">
      <h2>{run.label}</h2>
      <p>{run.about}</p>
      <div className="views" role="group" aria-label="views">
        {views.map((v) => (
          <button key={v} type="button" aria-pressed={v === view} onClick={() => setView(v)}>
            {viewName(v)}
          </button>
        ))}
      </div>
      {file && (
        <img
          className="frame"
          src={`./data/${file}`}
          alt={`${run.label}: ${viewName(view)}, at ${formatMs(frame.t_s)}`}
          width={960}
          height={540}
        />
      )}
      <Controls clock={clock} speeds={TUNNEL_SPEEDS} format={formatMs} step={0.001} />
      {stills.length > 0 && (
        <div className="stills">
          {stills.map((s) => (
            <figure key={s.file}>
              <img src={`./data/${s.file}`} alt={`${s.title}: ${s.subtitle}`} loading="lazy" />
              <figcaption>
                <strong>{s.title}.</strong> {s.caption}
              </figcaption>
            </figure>
          ))}
        </div>
      )}
    </section>
  );
}

const m = (v: number) => (Number.isInteger(v) ? String(v) : v.toFixed(1));

export function Tunnel({ load }: { load?: LoadOptions }) {
  const { data, problem } = useData<TunnelData>("tunnel.json", load);
  if (problem) return <p role="alert">{problem}</p>;
  if (!data) return <p>Loading</p>;
  const stillsOf = (c: TunnelCase) => data.stills.filter((s) => s.case.toLowerCase() === c.name.toLowerCase());
  return (
    <main>
      <h1>The wind tunnel</h1>
      <p className="purpose">
        FluidX3D, a lattice Boltzmann solver, on the PC's RTX 3060, with Max (every module on) in the air from six ways at
        10 m/s and hovering in still air. {data.note} The same runs play on the 3D drone in{" "}
        <a href="#/fly/tunnel/front">Fly it</a>, as particles carried through the flow and a speed slice that moves.
      </p>
      {data.fork_public && data.fork_url ? (
        <p className="muted credit">
          FluidX3D is Dr. Moritz Lehmann's:{" "}
          <a href={data.origin_url} target="_blank" rel="noreferrer">
            the original
          </a>
          . These runs come from my altered version of it,{" "}
          <a href={data.fork_url} target="_blank" rel="noreferrer">
            published here
          </a>{" "}
          as its license asks, and under the same license: no commercial or military use.
        </p>
      ) : (
        <p className="local-only">This page is a local preview for now.</p>
      )}
      {data.cases.length === 0 && data.stills.length === 0 && (
        <p>No tunnel runs on this machine yet: pcs14 tunnel, then pcs14 site --tunnel.</p>
      )}
      {data.cases.length > 0 && (
        <section aria-label="the cases">
          <h2>The seven cases</h2>
          <div className="scroll-x">
            <table className="short-columns">
              <thead>
                <tr>
                  <th scope="col">The air</th>
                  <th scope="col">What it is</th>
                  <th scope="col">Tunnel</th>
                  <th scope="col">Grid</th>
                  <th scope="col">Air simulated</th>
                  <th scope="col">Force along the wind</th>
                </tr>
              </thead>
              <tbody>
                {data.cases.map((c) => (
                  <tr key={c.name}>
                    <td>{c.label}</td>
                    <td>{c.about}</td>
                    <td>{c.box_m ? `${c.box_m.map(m).join(" x ")} m` : ""}</td>
                    <td>{c.grid ? `${c.grid}, ${c.cell_mm} mm` : ""}</td>
                    <td>{c.air_s != null ? `${c.air_s} s` : ""}</td>
                    <td>{c.force_n != null ? `${c.force_n.toFixed(1)} N` : "none, it's still air"}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
          <p className="muted">
            The force is FluidX3D's own, averaged over each run's last 40%. It's a picture's number: without a wall model
            FluidX3D runs 1.3 to 2 times high, and the tunnel is small next to the drone seen from above, which pushes
            the two vertical cases up more.
          </p>
        </section>
      )}
      <section aria-label="how it was run">
        <h2>How it was run</h2>
        <ul>
          <li>
            The drone is the CAD's watertight body with every module on, props and wires left out, voxelized into the
            grid. The air comes in along the tunnel at 10 m/s, and the drone is turned to meet it: nose first and pitched
            3.3 degrees the way it cruises, tail first pitched back, each side, top first and belly first.
          </li>
          <li>
            The hover is still air in a taller box, each prop an actuator disk: a disk of cells two thick pushing its
            quarter of the weight down on the air. The blades themselves at this resolution came out as flat paddles that
            pushed no air down.
          </li>
          <li>
            The Smagorinsky subgrid model handles the eddies too small for the grid, at a Reynolds number around
            260,000.
          </li>
          <li>
            Colors are turbo, the project's color map for flow, from still air to 17 m/s in the wind and 15 m/s in the
            hover.
          </li>
          <li>
            For the 3D view, each run also writes 64 snapshots of the flow over its last half, around the drone on 12 mm
            cells, and the averaged flow on 8 mm cells.
          </li>
        </ul>
        <p className="muted">
          The details are in the <a href="#/library/docs/log/2026-10-22-the-wind-tunnel-in-fly-it">wind tunnel log</a>,
          the <a href="#/library/docs/specs/2026-10-22-the-wind-tunnel-in-fly-it">spec</a> and the{" "}
          <a href="#/library/docs/decisions">decisions</a>. The drag numbers will come from OpenFOAM.
        </p>
      </section>
      {data.cases.map((c) => (
        <CaseView key={c.name} run={c} stills={stillsOf(c)} />
      ))}
    </main>
  );
}
