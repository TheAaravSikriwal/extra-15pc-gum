// Inside it: the controls beside the drone on the blueprint. The modules on and off, how far
// it's pulled apart, the wires' coloring, a harness to isolate and a wire in it to pick, and the
// card for whatever's picked.
import { Card } from "../explorer/Card";
import { harnessesOf } from "../explorer/explore";
import { shows } from "../explorer/logic";
import { WireCard } from "../explorer/WireCard";
import { numbersFor } from "./combos";
import { boardsOf } from "../pages/Wiring";
import { type DroneState, MODULES, type StageData } from "./Stage";

const CASES = ["hover", "cruise", "burst", "worst"];

export function InsidePanel({ state, data }: { state: DroneState; data: StageData }) {
  const picked = state.selected ? (data.pieces.get(state.selected) ?? null) : null;
  const numbers = numbersFor(data.spec, state.combination);
  const wires = data.wires3d?.wires ?? [];
  const wire = state.wire ? wires.find((w) => w.label === state.wire) : undefined;
  const inHarness = state.harness ? wires.filter((w) => w.harness === state.harness) : [];
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
      {wires.length > 0 && (
        <label>
          Harness{" "}
          <select
            aria-label="harness"
            value={state.harness ?? ""}
            onChange={(e) => {
              state.setHarness(e.target.value || null);
              state.pickWire(null);
            }}
          >
            <option value="">every one</option>
            {harnessesOf(wires).map((h) => (
              <option key={h}>{h}</option>
            ))}
          </select>
        </label>
      )}
      {inHarness.length > 0 && (
        <label>
          Wire{" "}
          <select aria-label="wire" value={state.wire ?? ""} onChange={(e) => state.pickWire(e.target.value || null)}>
            <option value="">click one, or pick it here</option>
            {inHarness.map((w) => (
              <option key={w.label} value={w.label}>
                {w.label}
              </option>
            ))}
          </select>
        </label>
      )}
      <label>
        Part{" "}
        <select aria-label="part" value={state.selected ?? ""} onChange={(e) => state.select(e.target.value || null)}>
          <option value="">click one, or pick it here</option>
          {(data.parts?.pieces ?? [])
            // the bundled routes give way to the wires, which have their own list
            .filter((p) => shows(p, state.modulesOn) && !(wires.length > 0 && p.kind === "wire"))
            .map((p) => (
              <option key={p.name} value={p.name}>
                {p.name}
              </option>
            ))}
        </select>
      </label>
      {wire ? (
        <WireCard wire={wire} sources={data.wires3d?.connectors ?? []} onClose={() => state.pickWire(null)} />
      ) : (
      <Card
        piece={picked}
        route={state.selected ? (data.routes.get(state.selected) ?? null) : null}
        combination={state.combination}
        kase={state.kase}
        boards={boardsOf(data.wiring, picked?.part_id ?? null)}
      />
      )}
    </aside>
  );
}
