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
import { Flight } from "../fly/Flight";
import { flyFraming, MODE_S } from "../fly/framing";
import type { DroneState, FlyData, StageData } from "./Stage";

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
  seconds: number;
}

interface Pose {
  target: THREE.Vector3;
  position: THREE.Vector3;
}

// every move the camera makes on its own, one at a time: easing in to a picked pin and back out
// once it's let go, and from inside the drone out to Fly it's floating framing and back
function CameraMoves({ focus, flying }: { focus: Vec3 | null; flying: boolean }) {
  const controls = useThree((s) => s.controls) as unknown as Controls | null;
  const camera = useThree((s) => s.camera);
  const job = useRef<Glide | null>(null);
  const beforePin = useRef<Pose | null>(null);
  const inside = useRef<Pose | null>(null);
  const go = useCallback(
    (target: THREE.Vector3, position: THREE.Vector3, seconds: number) => {
      if (!controls) return;
      job.current = {
        fromTarget: controls.target.clone(),
        fromPosition: camera.position.clone(),
        toTarget: target,
        toPosition: position,
        t: 0,
        seconds,
      };
    },
    [controls, camera],
  );
  useEffect(() => {
    if (!controls) return;
    if (focus) {
      beforePin.current ??= { target: controls.target.clone(), position: camera.position.clone() };
      const target = new THREE.Vector3(...focus);
      const away = camera.position.clone().sub(controls.target).normalize().multiplyScalar(CLOSE_M);
      go(target, target.clone().add(away), GLIDE_S);
    } else if (beforePin.current) {
      go(beforePin.current.target, beforePin.current.position, GLIDE_S);
      beforePin.current = null;
    }
  }, [focus, controls, camera, go]);
  useEffect(() => {
    if (!controls) return;
    if (flying) {
      // where it was inside the drone (before any pin), for coming back to
      const was = beforePin.current ?? { target: controls.target.clone(), position: camera.position.clone() };
      inside.current = { target: was.target.clone(), position: was.position.clone() };
      beforePin.current = null;
      const framed = flyFraming(was.position.toArray() as Vec3, [0, 0, 0]);
      go(new THREE.Vector3(...framed.target), new THREE.Vector3(...framed.position), MODE_S);
    } else if (inside.current) {
      go(inside.current.target, inside.current.position, MODE_S);
      inside.current = null;
    }
  }, [flying, controls, camera, go]);
  useFrame((_, delta) => {
    const j = job.current;
    if (!j || !controls) return;
    j.t = Math.min(1, j.t + delta / j.seconds);
    const e = easeInOut(j.t);
    controls.target.lerpVectors(j.fromTarget, j.toTarget, e);
    camera.position.lerpVectors(j.fromPosition, j.toPosition, e);
    controls.update();
    if (j.t >= 1) job.current = null;
  });
  return null;
}

export function StageCanvas({
  state,
  data,
  fly,
  load,
}: {
  state: DroneState;
  data: StageData;
  fly?: FlyData;
  load?: LoadOptions;
}) {
  const [turning, setTurning] = useState(true);
  const drone = useRef<THREE.Group>(null);
  const spins = useRef<Record<string, number> | null>(null);
  const flying = state.mode === "fly";
  const [focus, setFocus] = useState<Vec3 | null>(null);
  const { root } = useModel("drone.glb", load);
  const inside = state.mode === "inside";
  // phones get each wire as a thin line instead of a tube
  const light = useMemo(() => typeof window !== "undefined" && window.matchMedia?.("(max-width: 700px)").matches, []);
  // the fit frames the drone's height, so a screen taller than it is wide needs room for its width
  const margin = useMemo(() => {
    const aspect = typeof window === "undefined" ? 1.5 : window.innerWidth / window.innerHeight;
    return aspect < 1 ? 1.25 / aspect : 1.25;
  }, []);
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
      <Bounds fit clip observe margin={margin}>
        <group ref={drone}>
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
          spins={flying ? spins : undefined}
        />}
        </group>
      </Bounds>
      {flying && fly && (
        <Flight drone={drone} spins={spins} clip={fly.clip} playback={fly.playback} story={fly.story} onNumbers={fly.onNumbers} />
      )}
      {root && !flying && (
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
      <CameraMoves focus={inside ? focus : null} flying={flying} />
    </Canvas>
  );
}
