// Fly it: the scenarios down the side for the combination the modules make, grouped by the step
// that flew them, with what the playing one tests. Picking one changes the route, and the drone
// eases into it. (The numbers and the animation itself come with the fly mode's own task.)
import type { DroneState, StageData } from "./Stage";

export const STEPS: Record<number, string> = { 4: "Flight", 6: "Modules", 7: "Smart features" };

export interface ScenarioRow {
  name: string;
  step: number;
  what: string;
  flown: boolean;
}

// every scenario, in the flight sim's order, and whether a combination flew it on a firmware
export function scenariosFor(data: StageData, combination: string, firmware: string): ScenarioRow[] {
  const runs = data.flights?.runs ?? [];
  const about = new Map((data.flights?.about ?? []).map((a) => [a.name, a]));
  return (data.flights?.scenarios ?? []).map((name) => ({
    name,
    step: about.get(name)?.step ?? 4,
    what: about.get(name)?.what ?? "",
    flown: runs.some((r) => r.scenario === name && r.setup === combination && r.firmware === firmware && r.flown),
  }));
}

export function FlyPanel({ state, data }: { state: DroneState; data: StageData }) {
  const rows = scenariosFor(data, state.combination, state.firmware);
  const playing = rows.find((r) => r.name === state.scenario);
  const steps = [...new Set(rows.map((r) => r.step))];
  return (
    <aside className="stage-panel fly" aria-label="fly it">
      <p className="numbers-line">
        {state.combination}, {state.firmware === "mine" ? "my firmware" : "PX4"}
      </p>
      {playing && (
        <p className="about">
          <strong>{playing.name}.</strong> {playing.what}
          {!playing.flown && ` It wasn't flown in ${state.combination}.`}
        </p>
      )}
      <div className="scenarios" role="group" aria-label="scenarios">
        {steps.map((step) => {
          const flown = rows.filter((r) => r.step === step && r.flown);
          const not = rows.filter((r) => r.step === step && !r.flown);
          return (
            <section key={step} aria-label={STEPS[step] ?? `step ${step}`}>
              <h3>{STEPS[step] ?? `Step ${step}`}</h3>
              {flown.length > 0 && (
                <ul>
                  {flown.map((s) => (
                    <li key={s.name}>
                      <a
                        href={`#/fly/${encodeURIComponent(s.name)}`}
                        title={s.what}
                        aria-current={s.name === state.scenario ? "true" : undefined}
                      >
                        {s.name}
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
