// The drone in 3D, to click around: orbit and zoom, a click on any part for its card, the
// modules on and off, the exploded view, and the wires colored by how hard they work.
import { Bounds, OrbitControls } from "@react-three/drei";
import { Canvas } from "@react-three/fiber";
import { type ReactNode, useMemo, useState } from "react";

import type { LoadOptions } from "../data/load";
import type { Parts, Piece, Route, SpecSheet, Wires } from "../data/types";
import { useData } from "../data/useData";
import { Card } from "../explorer/Card";
import { shows } from "../explorer/logic";
import { useModel } from "../explorer/model";
import { DroneScene } from "../explorer/Scene";

const MODULES = ["V", "P", "C"];
const CASES = ["hover", "cruise", "burst", "worst"];

export interface ExplorerViewProps {
  parts: Parts;
  wires: Wires;
  spec?: SpecSheet | null; // for the numbers that follow the modules
  // the 3D part, given the state; the tests pass a stand-in, since jsdom has no WebGL
  view: (state: ViewState) => ReactNode;
}

export interface ViewState {
  pieces: Map<string, Piece>;
  routes: Map<string, Route>;
  modulesOn: Set<string>;
  explode: number;
  selected: string | null;
  combination: string;
  kase: string;
  select: (name: string | null) => void;
}

// the combination the modules switched on make
export function combinationFor(on: Set<string>): string {
  const names: Record<string, string> = {
    "": "base",
    V: "V",
    P: "P",
    C: "C",
    "V+P": "mission",
    "V+C": "V+C",
    "P+C": "P+C",
    "V+P+C": "max",
  };
  return names[MODULES.filter((m) => on.has(m)).join("+")];
}

// one line of what the switched-on modules make: the weight, the hover time and the verdict
export function numbersFor(spec: SpecSheet | null | undefined, combination: string): string | null {
  const c = spec?.combinations.find((x) => x.name === combination);
  if (!c) return null;
  const hover = c.checks.find((k) => k.name === "Hover time");
  const time = hover
    ? `, hovers ${hover.nominal.toFixed(1)} min${hover.pessimistic != null ? ` (${hover.pessimistic.toFixed(1)} pessimistic)` : ""}`
    : "";
  return `${c.name}: ${Math.round(c.mass_g)} g${time}, ${c.verdict}`;
}

export function ExplorerView({ parts, wires, spec, view }: ExplorerViewProps) {
  const [modulesOn, setModulesOn] = useState(() => new Set(MODULES));
  const [explode, setExplode] = useState(0);
  const [selected, select] = useState<string | null>(null);
  const [kase, setKase] = useState("hover");
  const pieces = useMemo(() => new Map(parts.pieces.map((p) => [p.name, p])), [parts]);
  const routes = useMemo(() => new Map(wires.routes.map((r) => [r.node, r])), [wires]);
  const combination = combinationFor(modulesOn);
  const picked = selected ? (pieces.get(selected) ?? null) : null;
  const toggle = (m: string) => {
    const next = new Set(modulesOn);
    if (next.has(m)) next.delete(m);
    else next.add(m);
    setModulesOn(next);
  };
  return (
    <div className="explorer">
      <div className="view">
        {view({ pieces, routes, modulesOn, explode, selected, combination, kase, select })}
      </div>
      <aside>
        {numbersFor(spec, combination) && <p className="numbers">{numbersFor(spec, combination)}</p>}
        <fieldset>
          <legend>Modules ({combination})</legend>
          {MODULES.map((m) => (
            <label key={m}>
              <input type="checkbox" checked={modulesOn.has(m)} onChange={() => toggle(m)} /> {m}
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
            value={explode}
            onChange={(e) => setExplode(Number(e.target.value))}
          />
        </label>
        <label>
          Wires colored for{" "}
          <select aria-label="case" value={kase} onChange={(e) => setKase(e.target.value)}>
            {CASES.map((c) => (
              <option key={c}>{c}</option>
            ))}
          </select>
        </label>
        <label>
          Part{" "}
          <select aria-label="part" value={selected ?? ""} onChange={(e) => select(e.target.value || null)}>
            <option value="">click one, or pick it here</option>
            {parts.pieces
              .filter((p) => shows(p, modulesOn))
              .map((p) => (
                <option key={p.name} value={p.name}>
                  {p.name}
                </option>
              ))}
          </select>
        </label>
        <Card
          piece={picked}
          route={selected ? (routes.get(selected) ?? null) : null}
          combination={combination}
          kase={kase}
        />
      </aside>
    </div>
  );
}

// the props turn at a few turns a second, for show (they really turn about 100)
const PROP_SHOW_SPIN = 12;

export function Explorer({ load }: { load?: LoadOptions }) {
  // it turns slowly until someone takes hold of it
  const [turning, setTurning] = useState(true);
  const parts = useData<Parts>("parts.json", load);
  const wires = useData<Wires>("wires.json", load);
  const spec = useData<SpecSheet>("spec.json", load);
  const model = useModel("drone.glb", load);
  const problem = parts.problem ?? wires.problem ?? model.problem;
  if (problem) return <p role="alert">{problem}</p>;
  if (!parts.data || !wires.data || !model.root) return <p>Loading the drone</p>;
  const root = model.root;
  return (
    <main className="wide">
      <h1>The drone, in 3D</h1>
      <ExplorerView
        parts={parts.data}
        wires={wires.data}
        spec={spec.data}
        view={(s) => (
          <Canvas camera={{ position: [0.55, 0.4, 0.65], fov: 35 }} dpr={[1, 2]}>
            <color attach="background" args={["#0b0b0b"]} />
            <hemisphereLight args={["#f4f4f2", "#2c2c2a", 1.4]} />
            <directionalLight position={[1, 2, 1.5]} intensity={2.2} />
            <directionalLight position={[-1, 0.5, -1]} intensity={0.8} />
            <Bounds fit clip observe margin={1.15}>
              <DroneScene
                root={root}
                pieces={s.pieces}
                routes={s.routes}
                modulesOn={s.modulesOn}
                explode={s.explode}
                selected={s.selected}
                combination={s.combination}
                kase={s.kase}
                onSelect={s.select}
                spin={PROP_SHOW_SPIN}
              />
            </Bounds>
            <OrbitControls makeDefault autoRotate={turning} autoRotateSpeed={0.6} onStart={() => setTurning(false)} />
          </Canvas>
        )}
      />
    </main>
  );
}
