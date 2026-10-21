// The drone in 3D, to click around: orbit and zoom, a click on any part for its card, the
// modules on and off, the exploded view, and the wires colored by how hard they work.
import { Bounds, OrbitControls } from "@react-three/drei";
import { Canvas } from "@react-three/fiber";
import { type ReactNode, useEffect, useMemo, useState } from "react";
import type * as THREE from "three";
import { GLTFLoader } from "three/examples/jsm/loaders/GLTFLoader.js";

import { loadBinary, type LoadOptions } from "../data/load";
import type { Parts, Piece, Route, Wires } from "../data/types";
import { useData } from "../data/useData";
import { Card } from "../explorer/Card";
import { shows } from "../explorer/logic";
import { DroneScene } from "../explorer/Scene";

const MODULES = ["V", "P", "C"];
const CASES = ["hover", "cruise", "burst", "worst"];

export interface ExplorerViewProps {
  parts: Parts;
  wires: Wires;
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

export function ExplorerView({ parts, wires, view }: ExplorerViewProps) {
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

function useModel(name: string, load?: LoadOptions) {
  const [root, setRoot] = useState<THREE.Object3D | null>(null);
  const [problem, setProblem] = useState<string | null>(null);
  useEffect(() => {
    let live = true;
    loadBinary(name, load)
      .then((bytes) => new GLTFLoader().parseAsync(bytes, ""))
      .then((gltf) => live && setRoot(gltf.scene))
      .catch((e: Error) => live && setProblem(e.message));
    return () => {
      live = false;
    };
  }, [name, load]);
  return { root, problem };
}

export function Explorer({ load }: { load?: LoadOptions }) {
  const parts = useData<Parts>("parts.json", load);
  const wires = useData<Wires>("wires.json", load);
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
              />
            </Bounds>
            <OrbitControls makeDefault />
          </Canvas>
        )}
      />
    </main>
  );
}
