// Fly it: what the playing run tests, its numbers as it flies (height, speed, the run's time and
// how fast it's playing, a bar per motor), its result in a line, the firmware that flew it, and
// the scenarios down the side for the combination the modules make, grouped by the step that
// flew them, each with a little drawing of its run and what it tests in a line. Picking one
// changes the route, and the drone eases into it. Above them, the wind tunnel: the air coming at
// the drone from each way it can, and the hover, each drawn as an arrow at the drone; picked,
// the drone holds still while the flow runs past it.
import { useMemo } from "react";

import type { Glyph } from "../data/types";
import { firstSentence } from "../fly/captions";
import { firmwaresFor, resultLine, speedWords } from "../fly/fly";
import { SLOW_MOTION } from "../fly/particles";
import { TURBO_GRADIENT } from "../fly/turbo";
import { tunnelLink } from "./modes";
import { Readout } from "./Readout";
import type { DroneState, FlyData, StageData } from "./Stage";

export const STEPS: Record<number, string> = { 4: "Flight", 6: "Modules", 7: "Smart features" };

export interface ScenarioRow {
  name: string;
  step: number;
  what: string;
  flown: boolean;
  glyph: Glyph | null; // its run's shape, from the combination's run or else any
}

// every scenario, in the flight sim's order, and whether a combination flew it on a firmware
export function scenariosFor(data: StageData, combination: string, firmware: string): ScenarioRow[] {
  const runs = data.flights?.runs ?? [];
  const about = new Map((data.flights?.about ?? []).map((a) => [a.name, a]));
  return (data.flights?.scenarios ?? []).map((name) => {
    const mine = runs.find((r) => r.scenario === name && r.setup === combination && r.firmware === firmware && r.flown);
    return {
      name,
      step: about.get(name)?.step ?? 4,
      what: about.get(name)?.what ?? "",
      flown: mine !== undefined,
      glyph: mine?.glyph ?? runs.find((r) => r.scenario === name && r.glyph)?.glyph ?? null,
    };
  });
}

// a run's shape in a line: its path from above, square, or its height across the whole box
function RunGlyph({ glyph }: { glyph: Glyph | null }) {
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

const slug = (name: string) => name.replace(/[^a-z0-9]+/gi, "-");

// the way the air comes at the drone, drawn small: the drone from above, nose up, for the four
// ways round it, and from the side for above, below and the hover, with the air's arrow
const ARROWS: Record<string, string> = {
  front: "M13 0.5V5 M11.2 3.2L13 5L14.8 3.2",
  back: "M13 15.5V11 M11.2 12.8L13 11L14.8 12.8",
  right: "M25.5 8H20 M21.8 6.2L20 8L21.8 9.8",
  left: "M0.5 8H6 M4.2 6.2L6 8L4.2 9.8",
  above: "M13 0.5V5.5 M11.2 3.7L13 5.5L14.8 3.7",
  below: "M13 15.5V10.5 M11.2 12.3L13 10.5L14.8 12.3",
  hover: "M9 10V15 M7.6 13.6L9 15L10.4 13.6 M17 10V15 M15.6 13.6L17 15L18.4 13.6",
};

function AirGlyph({ direction }: { direction: string }) {
  const side = direction === "above" || direction === "below" || direction === "hover";
  return (
    <svg className="glyph air" viewBox="0 0 26 16" aria-hidden="true">
      {side ? (
        <path className="drone" d="M7 8H19 M8 8V9.5 M18 8V9.5" />
      ) : (
        <path className="drone" d="M10 5L16 11 M16 5L10 11" />
      )}
      <path className="arrow" d={ARROWS[direction] ?? ""} />
    </svg>
  );
}

// the tunnel's case showing: what it is, the colors, FluidX3D's force, the slice switch
function TunnelNow({ state, fly }: { state: DroneState; fly: FlyData }) {
  const entry = fly.flowEntry;
  const flow = fly.flow;
  if (!entry) return null;
  return (
    <section className="tunnel-now hud-section" aria-label="the wind tunnel">
      <p className="about">
        <strong>{entry.label}.</strong> {entry.about} The particles ride the recorded flow, slowed down {SLOW_MOTION} times
        {entry.direction !== "hover" && ", with the ground going by at the same pace. Its props turn here, but the tunnel's body had none"}
        .
      </p>
      {flow && (
        <>
          <span className="hud-label">The air's speed</span>
          <div className="turbo-scale" aria-label={`colors from 0 to ${flow.color_max} m/s`}>
            <i style={{ background: TURBO_GRADIENT }} />
            <span>0</span>
            <span>{Math.round(flow.color_max / 2)}</span>
            <span>{flow.color_max} m/s</span>
          </div>
          {flow.force_n != null && (
            <p className="result">
              FluidX3D says {flow.force_n.toFixed(1)} N along the wind. That's a picture's number: it runs high without a
              wall model, and OpenFOAM will measure it.
            </p>
          )}
          {flow.slice && (
            <label className="hud-row toggle">
              <span className="hud-label">Slice</span>
              <span className="hud-hint">the speed on a plane through it, moving</span>
              <input type="checkbox" aria-label="speed slice" checked={state.slice} onChange={(e) => state.setSlice(e.target.checked)} />
            </label>
          )}
        </>
      )}
      {!flow && <p className="result">{entry.file ? "Loading the flow." : "This one isn't run in the tunnel yet."}</p>}
      {fly.credit && (
        <p className="credit">
          Run in{" "}
          <a href={fly.credit.fork} target="_blank" rel="noreferrer">
            my altered FluidX3D
          </a>
          . FluidX3D is{" "}
          <a href={fly.credit.origin} target="_blank" rel="noreferrer">
            Dr. Moritz Lehmann's
          </a>
          .
        </p>
      )}
    </section>
  );
}

const FIRMWARE: Record<string, string> = { mine: "My firmware", px4: "PX4" };

function Playing({ fly }: { fly: FlyData }) {
  const top = useMemo(() => Math.max(1, ...(fly.playback?.motors.flat() ?? [1])), [fly.playback]);
  const n = fly.playing;
  if (!fly.playback || !n) return null;
  return (
    <section className="playing hud-section" aria-label="playing">
      <dl className="numbers">
        <div>
          <dt>Height</dt>
          <dd>{n.height.toFixed(1)} m</dd>
        </div>
        <div>
          <dt>Speed</dt>
          <dd>{n.speed.toFixed(1)} m/s</dd>
        </div>
        <div>
          <dt>Time</dt>
          <dd>{n.time.toFixed(0)} s</dd>
        </div>
        <div>
          <dt>Playing</dt>
          <dd>{speedWords(n.factor)}</dd>
        </div>
      </dl>
      <span className="hud-label">Motors</span>
      <div className="motor-bars" aria-label="motors">
        {n.motors.map((m, k) => (
          <span key={k} title={`motor ${k + 1}: ${m.toFixed(0)} rad/s`}>
            <i style={{ height: `${Math.min(100, (m / top) * 100)}%` }} />
          </span>
        ))}
      </div>
      <p className="result">{resultLine(fly.playback)}</p>
    </section>
  );
}

export function FlyPanel({ state, data, fly }: { state: DroneState; data: StageData; fly?: FlyData }) {
  const rows = scenariosFor(data, state.combination, state.firmware);
  const firmwares = firmwaresFor(data.flights, state.combination, state.scenario);
  const playing = rows.find((r) => r.name === state.scenario);
  const steps = [...new Set(rows.map((r) => r.step))];
  return (
    <aside className="stage-panel fly" aria-label="fly it">
      <Readout
        title={state.tunnel ? `${state.combination}, wind tunnel` : `${state.combination}, ${state.firmware === "mine" ? "my firmware" : "PX4"}`}
        rows={[]}
        verdict={!state.tunnel && fly?.playback ? (fly.playback.passed ? "pass" : "fail") : null}
      />
      {state.tunnel && fly && <TunnelNow state={state} fly={fly} />}
      <div className="hud-section" hidden={!!state.tunnel}>
        {playing && (
          <p className="about">
            <strong>{playing.name}.</strong> {playing.what}
            {!playing.flown && ` It wasn't flown in ${state.combination} on ${FIRMWARE[state.firmware].toLowerCase()}.`}
          </p>
        )}
        {(firmwares.length > 1 || (firmwares.length === 1 && firmwares[0] !== state.firmware)) && (
          <div className="firmware-switch" role="group" aria-label="firmware">
            {firmwares.map((f) => (
              <button key={f} type="button" aria-pressed={state.firmware === f} onClick={() => state.setFirmware(f)}>
                {FIRMWARE[f]}
              </button>
            ))}
          </div>
        )}
      </div>
      {fly && !state.tunnel && <Playing fly={fly} />}
      <div className="scenarios hud-section" role="group" aria-label="scenarios">
        {fly && fly.flows.length > 0 && (
          <section aria-label="Wind tunnel">
            <h3 className="hud-label">Wind tunnel</h3>
            <ul>
              {fly.flows.map((f) => (
                <li key={f.name}>
                  {f.file ? (
                    <a
                      href={tunnelLink(f.direction)}
                      title={f.about}
                      aria-label={f.label}
                      aria-describedby={`air-${f.direction}`}
                      aria-current={state.tunnel === f.direction ? "true" : undefined}
                    >
                      <AirGlyph direction={f.direction} />
                      <span className="scenario-name">{f.label}</span>
                      <span className="scenario-what" id={`air-${f.direction}`}>
                        {f.about}
                      </span>
                    </a>
                  ) : (
                    <span className="pending" aria-label={`${f.label}, not run yet`}>
                      <AirGlyph direction={f.direction} />
                      <span className="scenario-name">{f.label}</span>
                      <span className="scenario-what">Not run in the tunnel yet.</span>
                    </span>
                  )}
                </li>
              ))}
            </ul>
          </section>
        )}
        {steps.map((step) => {
          const flown = rows.filter((r) => r.step === step && r.flown);
          const not = rows.filter((r) => r.step === step && !r.flown);
          return (
            <section key={step} aria-label={STEPS[step] ?? `step ${step}`}>
              <h3 className="hud-label">{STEPS[step] ?? `Step ${step}`}</h3>
              {flown.length > 0 && (
                <ul>
                  {flown.map((s) => (
                    <li key={s.name}>
                      <a
                        href={`#/fly/${encodeURIComponent(s.name)}`}
                        title={s.what}
                        aria-label={s.name}
                        aria-describedby={`what-${slug(s.name)}`}
                        aria-current={!state.tunnel && s.name === state.scenario ? "true" : undefined}
                      >
                        <RunGlyph glyph={s.glyph} />
                        <span className="scenario-name">{s.name}</span>
                        <span className="scenario-what" id={`what-${slug(s.name)}`}>
                          {firstSentence(s.what)}
                        </span>
                      </a>
                    </li>
                  ))}
                </ul>
              )}
              {not.length > 0 && (
                <p className="muted">
                  Not flown in {state.combination}: {not.map((s) => s.name).join(" · ")}
                </p>
              )}
            </section>
          );
        })}
      </div>
    </aside>
  );
}
