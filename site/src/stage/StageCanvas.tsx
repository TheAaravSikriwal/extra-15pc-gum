// The stage's 3D canvas: see-through, so the blueprint or the white space behind it shows, with
// the drone in the middle. Inside the drone it turns slowly until someone takes hold of it.
import { Bounds, OrbitControls } from "@react-three/drei";
import { Canvas } from "@react-three/fiber";
import { useState } from "react";
import type { LoadOptions } from "../data/load";
import { useModel } from "../explorer/model";

import { DroneScene } from "../explorer/Scene";
import type { DroneState, StageData } from "./Stage";

const PROP_SHOW_SPIN = 12;

export function StageCanvas({ state, data, load }: { state: DroneState; data: StageData; load?: LoadOptions }) {
  const [turning, setTurning] = useState(true);
  const { root } = useModel("drone.glb", load);
  const inside = state.mode === "inside";
  return (
    <Canvas camera={{ position: [0.55, 0.4, 0.65], fov: 35 }} dpr={[1, 2]} gl={{ alpha: true }}>
      <hemisphereLight args={["#f4f4f2", "#2c2c2a", 1.4]} />
      <directionalLight position={[1, 2, 1.5]} intensity={2.2} />
      <directionalLight position={[-1, 0.5, -1]} intensity={0.8} />
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
          onSelect={inside ? state.select : () => undefined}
          spin={PROP_SHOW_SPIN}
        />}
      </Bounds>
      <OrbitControls makeDefault autoRotate={inside && turning} autoRotateSpeed={0.6} onStart={() => setTurning(false)} />
    </Canvas>
  );
}
