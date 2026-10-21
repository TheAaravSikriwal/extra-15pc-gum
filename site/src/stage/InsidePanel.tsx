// Inside it: the controls beside the drone on the blueprint. The modules on and off, how far
// it's pulled apart, the wires' coloring, and the card for whatever's picked.
import { Card } from "../explorer/Card";
import { shows } from "../explorer/logic";
import { numbersFor } from "./combos";
import { boardsOf } from "../pages/Wiring";
import { type DroneState, MODULES, type StageData } from "./Stage";

const CASES = ["hover", "cruise", "burst", "worst"];

export function InsidePanel({ state, data }: { state: DroneState; data: StageData }) {
  const picked = state.selected ? (data.pieces.get(state.selected) ?? null) : null;
  const numbers = numbersFor(data.spec, state.combination);
  return (
    <aside className="stage-panel" aria-label="inside it">
      {numbers && <p className="numbers-line">{numbers}</p>}
      <fieldset>
        <legend>Modules ({state.combination})</legend>
        {MODULES.map((m) => (
          <label key={m}>
            <input type="checkbox" checked={state.modulesOn.has(m)} onChange={() => state.toggle(m)} /> {m}
          </label>
        ))}
      </fieldset>
      <label>
        Pulled apart{" "}
        <input
          type="range"
          aria-label="pulled apart"
          min={0}
          max={1}
          step={0.01}
          value={state.explode}
          onChange={(e) => state.setExplode(Number(e.target.value))}
        />
      </label>
      <label>
        Wires show{" "}
        <select
          aria-label="wires show"
          value={state.heat ? state.kase : ""}
          onChange={(e) => {
            state.setHeat(e.target.value !== "");
            if (e.target.value) state.setKase(e.target.value);
          }}
        >
          <option value="">their insulation</option>
          {CASES.map((c) => (
            <option key={c} value={c}>
              heating in {c}
            </option>
          ))}
        </select>
      </label>
      <label>
        Part{" "}
        <select aria-label="part" value={state.selected ?? ""} onChange={(e) => state.select(e.target.value || null)}>
          <option value="">click one, or pick it here</option>
          {(data.parts?.pieces ?? [])
            .filter((p) => shows(p, state.modulesOn))
            .map((p) => (
              <option key={p.name} value={p.name}>
                {p.name}
              </option>
            ))}
        </select>
      </label>
      <Card
        piece={picked}
        route={state.selected ? (data.routes.get(state.selected) ?? null) : null}
        combination={state.combination}
        kase={state.kase}
        boards={boardsOf(data.wiring, picked?.part_id ?? null)}
      />
    </aside>
  );
}
