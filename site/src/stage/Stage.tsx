// The stage: one drone, always in view. A full-screen 3D canvas that stays mounted whatever the
// route, the background behind it (the blueprint inside the drone, white space when it flies),
// and the interface floating over it. The drone's state (which modules are on, how far it's
// pulled apart, what's picked) lives here, so it carries from one mode into the other.
import { lazy, type ReactNode, Suspense, useMemo, useState } from "react";

import type { LoadOptions } from "../data/load";
import type { Flights, Parts, Piece, Route, SpecSheet, Wires, Wires3d, Wiring } from "../data/types";
import { useData } from "../data/useData";
import { combinationFor } from "./combos";
import { Blueprint } from "./Blueprint";
import { FlyPanel } from "./FlyPanel";
import { InsidePanel } from "./InsidePanel";
import { Menu } from "./Menu";
import { type Mode, modeOf, scenarioOf } from "./modes";

// three.js is about a megabyte, so the canvas loads after the page's first paint
const StageCanvas = lazy(() => import("./StageCanvas").then((m) => ({ default: m.StageCanvas })));

export const MODULES = ["V", "P", "C"];

export interface DroneState {
  mode: Mode;
  scenario: string;
  modulesOn: Set<string>;
  toggle: (module: string) => void;
  explode: number;
  setExplode: (x: number) => void;
  selected: string | null;
  select: (name: string | null) => void;
  kase: string;
  setKase: (k: string) => void;
  heat: boolean; // the wires colored by their heating in kase, or else in their insulation
  setHeat: (h: boolean) => void;
  combination: string;
  firmware: string;
  setFirmware: (f: string) => void;
}

export interface StageData {
  parts: Parts | null;
  wires: Wires | null;
  spec: SpecSheet | null;
  wiring: Wiring | null;
  flights: Flights | null;
  wires3d: Wires3d | null;
  pieces: Map<string, Piece>;
  routes: Map<string, Route>;
}

export function useDroneState(route: string[]): DroneState {
  const [modulesOn, setModulesOn] = useState(() => new Set(MODULES));
  const [explode, setExplode] = useState(0);
  const [selected, select] = useState<string | null>(null);
  const [kase, setKase] = useState("hover");
  const [heat, setHeat] = useState(false);
  const [firmware, setFirmware] = useState("mine");
  const toggle = (m: string) => {
    const next = new Set(modulesOn);
    if (next.has(m)) next.delete(m);
    else next.add(m);
    setModulesOn(next);
  };
  return {
    mode: modeOf(route),
    scenario: scenarioOf(route),
    modulesOn,
    toggle,
    explode,
    setExplode,
    selected,
    select,
    kase,
    setKase,
    heat,
    setHeat,
    combination: combinationFor(modulesOn),
    firmware,
    setFirmware,
  };
}

function useStageData(load?: LoadOptions): StageData {
  const parts = useData<Parts>("parts.json", load).data;
  const wires = useData<Wires>("wires.json", load).data;
  const spec = useData<SpecSheet>("spec.json", load).data;
  const wiring = useData<Wiring>("wiring.json", load).data;
  const flights = useData<Flights>("flights.json", load).data;
  const wires3d = useData<Wires3d>("wires3d.json", load).data;
  const pieces = useMemo(() => new Map((parts?.pieces ?? []).map((p) => [p.name, p])), [parts]);
  const routes = useMemo(() => new Map((wires?.routes ?? []).map((r) => [r.node, r])), [wires]);
  return { parts, wires, spec, wiring, flights, wires3d, pieces, routes };
}

function Intro() {
  return (
    <section className="stage-intro" aria-label="about">
      <h1>Extra 15pc Gum</h1>
      <p>
        My long-range quadcopter, with my own flight firmware. Every real part modeled, wired and flown in simulation,
        in public, before anything gets bought.
      </p>
    </section>
  );
}

export interface StageProps {
  route: string[];
  load?: LoadOptions;
  // the 3D part; the tests pass a stand-in, since jsdom has no WebGL
  scene?: (state: DroneState, data: StageData) => ReactNode;
}

export function Stage({ route, load, scene }: StageProps) {
  const state = useDroneState(route);
  const data = useStageData(load);
  const flyTo = `#/fly/${encodeURIComponent(state.scenario)}`;
  return (
    <div className={`stage ${state.mode}`} aria-hidden={state.mode === "page"} data-testid="stage">
      <div className="stage-back" aria-hidden="true">
        <div className="stage-layer stage-blueprint">
          <Blueprint />
        </div>
        <div className="stage-layer stage-white" />
      </div>
      <div className="stage-canvas">
        {scene ? (
          scene(state, data)
        ) : (
          <Suspense fallback={null}>
            <StageCanvas state={state} data={data} load={load} />
          </Suspense>
        )}
      </div>
      <header className="stage-top">
        <nav className="stage-switch" aria-label="mode">
          <a href="#/" aria-current={state.mode === "inside" ? "page" : undefined}>
            Inside it
          </a>
          <a href={flyTo} aria-current={state.mode === "fly" ? "page" : undefined}>
            Fly it
          </a>
        </nav>
      </header>
      <Menu />
      <Intro />
      {state.mode === "inside" && <InsidePanel state={state} data={data} />}
      {state.mode === "fly" && <FlyPanel state={state} data={data} />}
    </div>
  );
}

// re-exported for the canvas and the panels
export type { Mode };
