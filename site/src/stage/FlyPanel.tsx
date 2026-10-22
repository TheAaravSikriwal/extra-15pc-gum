// Fly it: what the playing run tests, its numbers as it flies (height, speed, the run's time and
// how fast it's playing, a bar per motor), its result in a line, the firmware that flew it, and
// the scenarios down the side for the combination the modules make, grouped by the step that
// flew them, each with a little drawing of its run and what it tests in a line. Picking one
// changes the route, and the drone eases into it.
import { useMemo } from "react";

import type { Glyph } from "../data/types";
import { firstSentence } from "../fly/captions";
import { firmwaresFor, resultLine, speedWords } from "../fly/fly";
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
        title={`${state.combination}, ${state.firmware === "mine" ? "my firmware" : "PX4"}`}
        rows={[]}
        verdict={fly?.playback ? (fly.playback.passed ? "pass" : "fail") : null}
      />
      <div className="hud-section">
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
      {fly && <Playing fly={fly} />}
      <div className="scenarios hud-section" role="group" aria-label="scenarios">
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
                        aria-current={s.name === state.scenario ? "true" : undefined}
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
