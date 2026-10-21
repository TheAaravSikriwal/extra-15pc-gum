// Fly it: the scenarios down the side, for the combination the modules make. Picking one changes
// the route, and the drone eases into it. (The numbers and the animation itself come with the
// fly mode's own task.)
import type { DroneState, StageData } from "./Stage";

// the scenarios flown for a combination on a firmware, in the flight sim's order
export function scenariosFor(data: StageData, combination: string, firmware: string): { name: string; flown: boolean }[] {
  const runs = data.flights?.runs ?? [];
  const names = data.flights?.scenarios ?? [];
  return names.map((name) => ({
    name,
    flown: runs.some((r) => r.scenario === name && r.setup === combination && r.firmware === firmware && r.flown),
  }));
}

export function FlyPanel({ state, data }: { state: DroneState; data: StageData }) {
  const list = scenariosFor(data, state.combination, state.firmware);
  return (
    <aside className="stage-panel fly" aria-label="fly it">
      <p className="numbers-line">
        {state.combination}, {state.firmware === "mine" ? "my firmware" : "PX4"}
      </p>
      <ul className="scenarios" aria-label="scenarios">
        {list.map((s) => (
          <li key={s.name}>
            {s.flown ? (
              <a href={`#/fly/${encodeURIComponent(s.name)}`} aria-current={s.name === state.scenario ? "true" : undefined}>
                {s.name}
              </a>
            ) : (
              <span className="muted" title={`not flown in ${state.combination}`}>
                {s.name}
              </span>
            )}
          </li>
        ))}
      </ul>
    </aside>
  );
}
