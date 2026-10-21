// The wind tunnel: each case's frames along the way, played on the clock in slow motion (half
// a second of air takes half a minute), and the stills with what each one says. Pictures, not
// measurements: the drag numbers come from OpenFOAM.
import { useEffect, useMemo, useState } from "react";

import type { LoadOptions } from "../data/load";
import type { Tunnel as TunnelData, TunnelCase, TunnelFrame } from "../data/types";
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

export function CaseView({ run, now }: { run: TunnelCase; now?: () => number }) {
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
    </section>
  );
}

export function Tunnel({ load }: { load?: LoadOptions }) {
  const { data, problem } = useData<TunnelData>("tunnel.json", load);
  if (problem) return <p role="alert">{problem}</p>;
  if (!data) return <p>Loading</p>;
  return (
    <main>
      <h1>The wind tunnel</h1>
      <p className="note">{data.note}</p>
      {!data.fork_public && <p className="local-only">This page is a local preview for now.</p>}
      {data.cases.length === 0 && data.stills.length === 0 && (
        <p>No tunnel runs on this machine yet: pcs14 tunnel, then pcs14 site --tunnel.</p>
      )}
      {data.cases.map((c) => (
        <CaseView key={c.name} run={c} />
      ))}
      {data.stills.length > 0 && (
        <section aria-label="the stills" className="stills">
          <h2>The stills</h2>
          {data.stills.map((s) => (
            <figure key={s.file}>
              <img src={`./data/${s.file}`} alt={`${s.title}: ${s.subtitle}`} loading="lazy" />
              <figcaption>
                <strong>{s.number}</strong> {s.caption}
              </figcaption>
            </figure>
          ))}
        </section>
      )}
    </main>
  );
}
