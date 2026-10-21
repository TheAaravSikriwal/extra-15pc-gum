// One scenario in one combination, played back as if it were happening: PX4's run and mine
// together on one clock, the drones in 3D, the charts scrolling, the events popping up.
import { OrbitControls } from "@react-three/drei";
import { Canvas, useFrame, useThree } from "@react-three/fiber";
import { type ReactNode, useEffect, useMemo, useState } from "react";
import * as THREE from "three";
import type { OrbitControls as OrbitControlsImpl } from "three-stdlib";

import { TimeChart } from "../charts/TimeChart";
import { loadData, type LoadOptions } from "../data/load";
import type { Flights, Playback } from "../data/types";
import { useData } from "../data/useData";
import { COLORS, FlightScene } from "../flights/FlightScene";
import { chapters, duration, eventsSoFar, indexAt, series, toThree } from "../flights/playback";
import { Clock, useClockTime } from "../play/clock";
import { Controls, formatTime } from "../play/Controls";

const NAMES: Record<string, string> = { px4: "PX4", mine: "My firmware" };

export function useRuns(setup: string, scenario: string, load?: LoadOptions) {
  const index = useData<Flights>("flights.json", load);
  const [runs, setRuns] = useState<Playback[] | null>(null);
  const [problem, setProblem] = useState<string | null>(null);
  useEffect(() => {
    if (!index.data) return;
    const files = index.data.runs
      .filter((r) => r.setup === setup && r.scenario === scenario && r.file)
      .map((r) => r.file as string);
    if (!files.length) {
      setProblem(`no flown runs of ${scenario} in ${setup}`);
      return;
    }
    let live = true;
    Promise.all(files.map((f) => loadData<Playback>(f, load)))
      .then((found) => live && setRuns(found))
      .catch((e: Error) => live && setProblem(e.message));
    return () => {
      live = false;
    };
  }, [index.data, setup, scenario, load]);
  return { runs, problem: index.problem ?? problem };
}

export function FlightView({ runs, view }: { runs: Playback[]; view: (time: number) => ReactNode }) {
  const clock = useMemo(() => new Clock({ duration: duration(runs), chapters: chapters(runs) }), [runs]);
  const time = useClockTime(clock);
  const all = runs.map((p) => ({ p, s: series(p) }));
  const lines = (pick: "height" | "speed" | "motors") =>
    all.map(({ p, s }) => ({ name: NAMES[p.firmware] ?? p.firmware, t: p.t, v: s[pick], color: COLORS[p.firmware] }));
  const d = clock.duration;
  return (
    <div className="flight">
      <div className="view">{view(time)}</div>
      <Controls clock={clock} />
      <div className="legend">
        {runs.map((p) => (
          <span key={p.firmware} style={{ color: COLORS[p.firmware] }}>
            {NAMES[p.firmware]}: {p.passed ? "pass" : "fail"}
          </span>
        ))}
      </div>
      <TimeChart title="Height" unit="m" series={lines("height")} time={time} duration={d} window={60} />
      <TimeChart title="Speed" unit="m/s" series={lines("speed")} time={time} duration={d} window={60} />
      <TimeChart title="Motors, on average" unit="rad/s" series={lines("motors")} time={time} duration={d} window={60} />
      <div className="columns">
        {runs.map((p) => (
          <section key={p.firmware} aria-label={`${NAMES[p.firmware]} events`}>
            <h3>{NAMES[p.firmware]}</h3>
            <ol className="events">
              {eventsSoFar(p, time)
                .slice(-8)
                .map((e) => (
                  <li key={`${e.name}-${e.at}`}>
                    <span className="at">{formatTime(e.at)}</span> {e.name}
                  </li>
                ))}
            </ol>
            <ul className="findings">
              {p.findings.map((f) => (
                <li key={f.check} className={f.passed ? "pass" : "fail"}>
                  {f.check}: {f.detail}
                </li>
              ))}
            </ul>
          </section>
        ))}
      </div>
    </div>
  );
}

// keeps the camera with the drone as it flies: the target eases onto it, and the camera moves
// along with the target, so it stays as close as it was
function Follow({ runs, time }: { runs: Playback[]; time: number }) {
  const controls = useThree((s) => s.controls) as OrbitControlsImpl | null;
  const camera = useThree((s) => s.camera);
  const target = useMemo(() => new THREE.Vector3(), []);
  const before = useMemo(() => new THREE.Vector3(), []);
  useFrame(() => {
    if (!controls) return;
    const at = runs.map((p) => toThree(p.position[indexAt(p, time)]));
    target.set(...(at[0] ?? [0, 0, 0]));
    before.copy(controls.target);
    controls.target.lerp(target, 0.15);
    camera.position.add(controls.target.clone().sub(before));
    controls.update();
  });
  return null;
}

export function FlightRun({ setup, scenario, load }: { setup: string; scenario: string; load?: LoadOptions }) {
  const { runs, problem } = useRuns(setup, scenario, load);
  if (problem) return <p role="alert">{problem}</p>;
  if (!runs) return <p>Loading the flight</p>;
  return (
    <main className="wide">
      <p>
        <a href="#/flights">Every flight</a>
      </p>
      <h1>
        {scenario}, {setup}
      </h1>
      <FlightView
        runs={runs}
        view={(time) => (
          <Canvas camera={{ position: [6, 5, 8], fov: 40 }} dpr={[1, 2]}>
            <color attach="background" args={["#0b0b0b"]} />
            <hemisphereLight args={["#f4f4f2", "#2c2c2a", 1.2]} />
            <directionalLight position={[5, 10, 5]} intensity={1.5} />
            <FlightScene runs={runs} time={time} />
            <OrbitControls makeDefault />
            <Follow runs={runs} time={time} />
          </Canvas>
        )}
      />
    </main>
  );
}
