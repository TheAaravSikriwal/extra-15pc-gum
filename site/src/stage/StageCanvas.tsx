// The stage's 3D canvas: see-through, so the blueprint or the white space behind it shows, with
// the drone in the middle. Inside the drone it turns slowly until someone takes hold of it, and
// a picked wire draws the camera in to its pin.
// The light is made here, not fetched: a room's soft reflections for the metal and the clear
// coats, a key light, and a soft shadow under the drone.
import { Bounds, ContactShadows, OrbitControls } from "@react-three/drei";
import { Canvas, useFrame, useThree } from "@react-three/fiber";
import { useCallback, useEffect, useMemo, useRef, useState } from "react";
import * as THREE from "three";
import { RoomEnvironment } from "three/examples/jsm/environments/RoomEnvironment.js";
import type { OrbitControls as Controls } from "three/examples/jsm/controls/OrbitControls.js";

import type { LoadOptions } from "../data/load";
import { easeInOut } from "../explorer/explore";
import { useModel } from "../explorer/model";
import { DroneScene } from "../explorer/Scene";
import type { Vec3 } from "../explorer/wires3d";
import type { DroneState, StageData } from "./Stage";

const PROP_SHOW_SPIN = 12;
const GLIDE_S = 0.9;
const CLOSE_M = 0.12; // how far from a picked pin the camera stops

// a room's light, blurred into an environment map, for the reflections
function Room() {
  const { gl, scene } = useThree();
  useEffect(() => {
    const pmrem = new THREE.PMREMGenerator(gl);
    const env = pmrem.fromScene(new RoomEnvironment(), 0.04).texture;
    scene.environment = env;
    scene.environmentIntensity = 0.6;
    return () => {
      scene.environment = null;
      env.dispose();
      pmrem.dispose();
    };
  }, [gl, scene]);
  return null;
}

interface Glide {
  fromTarget: THREE.Vector3;
  fromPosition: THREE.Vector3;
  toTarget: THREE.Vector3;
  toPosition: THREE.Vector3;
  t: number;
}

// the camera easing in to a point, looking at it from the way it already looks, and back out to
// where it was once nothing's picked
function GlideTo({ to }: { to: Vec3 | null }) {
  const controls = useThree((s) => s.controls) as unknown as Controls | null;
  const camera = useThree((s) => s.camera);
  const job = useRef<Glide | null>(null);
  const home = useRef<{ target: THREE.Vector3; position: THREE.Vector3 } | null>(null);
  useEffect(() => {
    if (!controls) return;
    const from = { fromTarget: controls.target.clone(), fromPosition: camera.position.clone(), t: 0 };
    if (to) {
      home.current ??= { target: controls.target.clone(), position: camera.position.clone() };
      const toTarget = new THREE.Vector3(...to);
      const away = camera.position.clone().sub(controls.target).normalize().multiplyScalar(CLOSE_M);
      job.current = { ...from, toTarget, toPosition: toTarget.clone().add(away) };
    } else if (home.current) {
      job.current = { ...from, toTarget: home.current.target, toPosition: home.current.position };
      home.current = null;
    }
  }, [to, controls, camera]);
  useFrame((_, delta) => {
    const j = job.current;
    if (!j || !controls) return;
    j.t = Math.min(1, j.t + delta / GLIDE_S);
    const e = easeInOut(j.t);
    controls.target.lerpVectors(j.fromTarget, j.toTarget, e);
    camera.position.lerpVectors(j.fromPosition, j.toPosition, e);
    controls.update();
    if (j.t >= 1) job.current = null;
  });
  return null;
}

export function StageCanvas({ state, data, load }: { state: DroneState; data: StageData; load?: LoadOptions }) {
  const [turning, setTurning] = useState(true);
  const [focus, setFocus] = useState<Vec3 | null>(null);
  const { root } = useModel("drone.glb", load);
  const inside = state.mode === "inside";
  // phones get each wire as a thin line instead of a tube
  const light = useMemo(() => typeof window !== "undefined" && window.matchMedia?.("(max-width: 700px)").matches, []);
  // where the assembled drone's feet are, for its shadow
  const floor = useMemo(() => (root ? new THREE.Box3().setFromObject(root).min.y : 0), [root]);
  // a new focus only when the pin itself moves, so the glide runs once per pick
  const onFocus = useCallback((at: Vec3 | null) => {
    setFocus((was) => (at && was && at.every((v, i) => Math.abs(v - was[i]) < 1e-6) ? was : at));
    if (at) setTurning(false);
  }, []);
  return (
    <Canvas camera={{ position: [0.55, 0.4, 0.65], fov: 35 }} dpr={[1, 2]} gl={{ alpha: true }}>
      <Room />
      <hemisphereLight args={["#f4f4f2", "#2c2c2a", 0.6]} />
      <directionalLight position={[1, 2, 1.5]} intensity={2.4} />
      <directionalLight position={[-1, 0.5, -1]} intensity={0.7} />
      <Bounds fit clip observe margin={1.25}>
        {root && <DroneScene
          root={root}
          pieces={data.pieces}
          routes={data.routes}
          modulesOn={state.modulesOn}
          explode={inside ? state.explode : 0}
          selected={inside ? state.selected : null}
          combination={state.combination}
          kase={state.kase}
          heat={state.heat}
          wires={data.wires3d?.wires}
          light={light}
          pickedWire={inside ? state.wire : null}
          harness={inside ? state.harness : null}
          onPickWire={inside ? state.pickWire : undefined}
          onFocus={onFocus}
          onSelect={inside ? state.select : () => undefined}
          spin={PROP_SHOW_SPIN}
        />}
      </Bounds>
      {root && (
        <ContactShadows
          position={[0, floor - 0.002, 0]}
          scale={0.9}
          blur={2.4}
          far={0.4}
          resolution={512}
          opacity={inside ? 0.45 : 0.25}
          color={inside ? "#061a33" : "#5a5a55"}
        />
      )}
      <OrbitControls makeDefault autoRotate={inside && turning} autoRotateSpeed={0.6} onStart={() => setTurning(false)} />
      <GlideTo to={inside ? focus : null} />
    </Canvas>
  );
}
