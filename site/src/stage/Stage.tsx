// The stage: one drone, always in view. A full-screen 3D canvas that stays mounted whatever the
// route, the background behind it (the blueprint inside the drone, white space when it flies),
// and the interface floating over it. The drone's state (which modules are on, how far it's
// pulled apart, what's picked) lives here, so it carries from one mode into the other.
import { lazy, type MutableRefObject, type ReactNode, Suspense, useEffect, useMemo, useRef, useState } from "react";

import type { LoadOptions } from "../data/load";
import type {
  Flights,
  Parts,
  Piece,
  Playback,
  Route,
  SpecSheet,
  Tunnel,
  TunnelFlow,
  TunnelFlowEntry,
  Wires,
  Wires3d,
  Wiring,
} from "../data/types";
import { useData, useOptionalData } from "../data/useData";
import { clipOf } from "../fly/clip";
import { runFor, storyProps } from "../fly/fly";
import type { Live, Playing } from "../fly/Flight";
import { usePlayback } from "../fly/usePlayback";
import { combinationFor } from "./combos";
import { Blueprint } from "./Blueprint";
import { ControlsHint } from "./ControlsHint";
import { FlyOverlay } from "./FlyOverlay";
import { FlyPanel } from "./FlyPanel";
import { InsidePanel } from "./InsidePanel";
import { Menu } from "./Menu";
import { modulesOf } from "../explorer/logic";
import { type Mode, modeOf, scenarioOf, setupOf, tunnelOf } from "./modes";

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
  wire: string | null; // a picked wire, by its label
  pickWire: (label: string | null) => void;
  harness: string | null; // one harness isolated
  setHarness: (h: string | null) => void;
  kase: string;
  setKase: (k: string) => void;
  heat: boolean; // the wires colored by their heating in kase, or else in their insulation
  setHeat: (h: boolean) => void;
  combination: string;
  firmware: string;
  setFirmware: (f: string) => void;
  tunnel: string | null; // where the air comes from, when the wind tunnel's flow is showing
  slice: boolean; // the tunnel's speed slice through the drone, shown
  setSlice: (s: boolean) => void;
  setModules: (modules: string[]) => void;
}

export interface StageData {
  parts: Parts | null;
  wires: Wires | null;
  spec: SpecSheet | null;
  wiring: Wiring | null;
  flights: Flights | null;
  wires3d: Wires3d | null;
  tunnel: Tunnel | null;
  pieces: Map<string, Piece>;
  routes: Map<string, Route>;
}

export function useDroneState(route: string[]): DroneState {
  const [modulesOn, setModulesOn] = useState(() => new Set(MODULES));
  const [explode, setExplode] = useState(0);
  const [selected, setSelected] = useState<string | null>(null);
  const [wire, setWire] = useState<string | null>(null);
  const [harness, setHarness] = useState<string | null>(null);
  // a piece or a wire is picked, not both
  const select = (name: string | null) => {
    setSelected(name);
    setWire(null);
  };
  const pickWire = (label: string | null) => {
    setWire(label);
    if (label) setSelected(null);
  };
  const [kase, setKase] = useState("hover");
  const [heat, setHeat] = useState(false);
  // a link that names a combination switches the modules to it
  const setup = setupOf(route);
  useEffect(() => {
    if (setup) setModulesOn(new Set(modulesOf(setup)));
  }, [setup]);
  const [firmware, setFirmware] = useState("mine");
  const [slice, setSlice] = useState(true);
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
    wire,
    pickWire,
    harness,
    setHarness,
    kase,
    setKase,
    heat,
    setHeat,
    combination: combinationFor(modulesOn),
    firmware,
    setFirmware,
    tunnel: tunnelOf(route),
    slice,
    setSlice,
    setModules: (modules) => setModulesOn(new Set(modules)),
  };
}

function useStageData(load?: LoadOptions): StageData {
  const parts = useData<Parts>("parts.json", load).data;
  const wires = useData<Wires>("wires.json", load).data;
  const spec = useData<SpecSheet>("spec.json", load).data;
  const wiring = useData<Wiring>("wiring.json", load).data;
  const flights = useData<Flights>("flights.json", load).data;
  const wires3d = useData<Wires3d>("wires3d.json", load).data;
  const tunnel = useData<Tunnel>("tunnel.json", load).data;
  const pieces = useMemo(() => new Map((parts?.pieces ?? []).map((p) => [p.name, p])), [parts]);
  const routes = useMemo(() => new Map((wires?.routes ?? []).map((r) => [r.node, r])), [wires]);
  return { parts, wires, spec, wiring, flights, wires3d, tunnel, pieces, routes };
}

function Intro({ flying }: { flying: boolean }) {
  return (
    <section className="stage-intro" aria-label="about">
      <h1>Extra 15pc Gum</h1>
      <p>
        My long-range quadcopter, with my own flight firmware. Every real part modeled, wired and flown in simulation,
        in public, before anything gets bought.
      </p>
      {flying && <ControlsHint />}
    </section>
  );
}

// what Fly it plays: the run for the modules, the scenario and the firmware, as a loop
export interface FlyData {
  playback: Playback | null;
  clip: ReturnType<typeof clipOf> | null;
  story: ReturnType<typeof storyProps> | null;
  playing: Playing | null;
  onNumbers: (n: Playing) => void;
  live: MutableRefObject<Live | null>; // where it is this frame, for the drawings under it
  seek: MutableRefObject<number | null>; // a loop time to jump to
  flows: TunnelFlowEntry[]; // the wind tunnel's cases, one for each way the air comes from
  flowEntry: TunnelFlowEntry | null; // the one showing
  flow: TunnelFlow | null;
  credit: { origin: string; fork: string } | null; // FluidX3D's, and my altered version's
}

function useFly(state: DroneState, data: StageData, load?: LoadOptions): FlyData {
  const flows = data.tunnel?.flows ?? [];
  const flowEntry = state.mode === "fly" && state.tunnel ? (flows.find((f) => f.direction === state.tunnel) ?? null) : null;
  const flow = useOptionalData<TunnelFlow>(flowEntry?.file ?? null, load); // none if it's not run yet
  // the wind tunnel holds the drone still in the air, so no run plays while it shows
  const run =
    state.mode === "fly" && !state.tunnel ? runFor(data.flights, state.combination, state.scenario, state.firmware) : null;
  const playback = usePlayback(run?.file ?? null, load);
  const clip = useMemo(() => (playback ? clipOf(playback) : null), [playback]);
  const story = useMemo(() => (playback ? storyProps(playback) : null), [playback]);
  const [playing, setPlaying] = useState<Playing | null>(null);
  useEffect(() => setPlaying(null), [playback]);
  const live = useRef<Live | null>(null);
  const seek = useRef<number | null>(null);
  const tunnel = data.tunnel;
  const credit =
    tunnel?.fork_public && tunnel.fork_url
      ? { origin: tunnel.origin_url ?? "https://github.com/ProjectPhysX/FluidX3D", fork: tunnel.fork_url }
      : null;
  return { playback, clip, story, playing, onNumbers: setPlaying, live, seek, flows, flowEntry, flow, credit };
}

// the panel beside the drone, which on a phone becomes a drawer along the bottom: closed, it
// leaves the drone the screen with just its handle showing
function Drawer({ open, onToggle, children }: { open: boolean; onToggle: () => void; children: ReactNode }) {
  return (
    <div className={`stage-drawer${open ? " open" : ""}`}>
      <button className="drawer-handle" type="button" aria-expanded={open} onClick={onToggle}>
        {open ? "Hide the controls" : "Show the controls"}
      </button>
      {children}
    </div>
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
  const fly = useFly(state, data, load);
  const [drawer, setDrawer] = useState(false);
  // on a phone, picking a run closes the drawer so the drone's there to watch it fly
  useEffect(() => setDrawer(false), [state.scenario, state.combination, state.tunnel]);
  // the tunnel ran around one combination, so the drone shows that one while its flow does
  // (on the combination's name only: setModules is new each render)
  const flowSetup = fly.flow?.setup.toLowerCase();
  const setModules = state.setModules;
  useEffect(() => {
    if (flowSetup && modulesOf(flowSetup).length) setModules(modulesOf(flowSetup));
  }, [flowSetup]);
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
            <StageCanvas state={state} data={data} fly={fly} load={load} />
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
      <Intro flying={state.mode === "fly"} />
      {state.mode === "fly" && <FlyOverlay fly={fly} />}
      {state.mode !== "page" && (
        <Drawer open={drawer} onToggle={() => setDrawer(!drawer)}>
          {state.mode === "inside" && <InsidePanel state={state} data={data} />}
          {state.mode === "fly" && <FlyPanel state={state} data={data} fly={fly} />}
        </Drawer>
      )}
    </div>
  );
}

// re-exported for the canvas and the panels
export type { Mode };
