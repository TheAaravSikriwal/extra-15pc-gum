// The stage's 3D canvas: see-through, so the blueprint or the white space behind it shows, with
// the drone in the middle. Inside the drone it turns slowly until someone takes hold of it.
// The light is made here, not fetched: a room's soft reflections for the metal and the clear
// coats, a key light, and a soft shadow under the drone.
import { Bounds, ContactShadows, OrbitControls } from "@react-three/drei";
import { Canvas, useThree } from "@react-three/fiber";
import { useEffect, useMemo, useState } from "react";
import * as THREE from "three";
import { RoomEnvironment } from "three/examples/jsm/environments/RoomEnvironment.js";

import type { LoadOptions } from "../data/load";
import { useModel } from "../explorer/model";
import { DroneScene } from "../explorer/Scene";
import type { DroneState, StageData } from "./Stage";

const PROP_SHOW_SPIN = 12;

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

export function StageCanvas({ state, data, load }: { state: DroneState; data: StageData; load?: LoadOptions }) {
  const [turning, setTurning] = useState(true);
  const { root } = useModel("drone.glb", load);
  const inside = state.mode === "inside";
  // where the assembled drone's feet are, for its shadow
  const floor = useMemo(() => (root ? new THREE.Box3().setFromObject(root).min.y : 0), [root]);
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
    </Canvas>
  );
}
