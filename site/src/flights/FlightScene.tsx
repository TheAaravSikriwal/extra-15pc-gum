// Both runs of a scenario in one scene: each drone flying its logged path, turning with its
// logged attitude, on the page's clock, with the path behind it. PX4's in fog, mine in
// spearmint. Each drone is a light stand-in (arms, props, a nose) until the CAD's model has
// loaded, then the model itself, with only the modules its combination flies with.
import { useMemo } from "react";
import * as THREE from "three";

import type { Piece, Playback } from "../data/types";
import { modulesOf, shows } from "../explorer/logic";
import { nodeName } from "../explorer/Scene";
import { indexAt, toThree } from "./playback";

export interface DroneModel {
  root: THREE.Object3D; // the CAD's GLB
  pieces: Map<string, Piece>;
}

// a copy of the model in one run's color, its combination's modules on and the rest off
function modelFor(model: DroneModel, setup: string, color: string): THREE.Object3D {
  const copy = model.root.clone(true);
  const on = new Set(modulesOf(setup));
  const byNode = new Map([...model.pieces.keys()].map((n) => [nodeName(n), n]));
  const material = new THREE.MeshStandardMaterial({ color, metalness: 0.1, roughness: 0.7 });
  copy.traverse((node) => {
    const name = byNode.get(node.name);
    if (name) node.visible = shows(model.pieces.get(name) as Piece, on);
    if (node instanceof THREE.Mesh) node.material = material;
  });
  return copy;
}

export const COLORS: Record<string, string> = { px4: "#b4b2a9", mine: "#3ddc97" };

// the log's quaternion (x, y, z, w; the body, forward-left-up, to east-north-up) in three.js's
// frame, where the stand-in drone is built facing +x with its left along -z
const TO_THREE = new THREE.Quaternion().setFromAxisAngle(new THREE.Vector3(1, 0, 0), -Math.PI / 2);
export function attitudeIn3(q: number[]): THREE.Quaternion {
  const logged = new THREE.Quaternion(q[0], q[1], q[2], q[3]);
  return TO_THREE.clone().multiply(logged).multiply(TO_THREE.clone().invert());
}

function StandIn({ color }: { color: string }) {
  const arm = 0.21; // about the drone's own half-diagonal, m
  return (
    <group name="stand-in">
      {[45, 135, 225, 315].map((deg) => {
        const a = (deg * Math.PI) / 180;
        return (
          <group key={deg}>
            <mesh position={[(arm / 2) * Math.cos(a), 0, (-arm / 2) * Math.sin(a)]} rotation={[0, a, 0]}>
              <boxGeometry args={[arm, 0.012, 0.02]} />
              <meshStandardMaterial color={color} />
            </mesh>
            <mesh position={[arm * Math.cos(a), 0.02, -arm * Math.sin(a)]}>
              <cylinderGeometry args={[0.127, 0.127, 0.004, 24]} />
              <meshStandardMaterial color={color} transparent opacity={0.35} />
            </mesh>
          </group>
        );
      })}
      <mesh position={[0.09, 0, 0]}>
        <boxGeometry args={[0.06, 0.03, 0.03]} />
        <meshStandardMaterial color="#e64fa0" />
      </mesh>
    </group>
  );
}

export function FlightScene({ runs, time, model }: { runs: Playback[]; time: number; model?: DroneModel | null }) {
  const drones = useMemo(
    () => runs.map((p) => (model ? modelFor(model, p.setup, COLORS[p.firmware] ?? "#f4f4f2") : null)),
    [runs, model],
  );
  const paths = useMemo(
    () =>
      runs.map((p) => {
        const g = new THREE.BufferGeometry().setFromPoints(
          p.position.map((x) => new THREE.Vector3(...toThree(x))),
        );
        return new THREE.Line(g, new THREE.LineBasicMaterial({ color: COLORS[p.firmware] ?? "#f4f4f2" }));
      }),
    [runs],
  );
  return (
    <group>
      {paths.map((line, k) => (
        <primitive key={runs[k].firmware} object={line} />
      ))}
      {runs.map((p, n) => {
        const k = indexAt(p, time);
        const drone = drones[n];
        return (
          <group
            key={p.firmware}
            name={`drone ${p.firmware}`}
            position={toThree(p.position[k])}
            quaternion={attitudeIn3(p.attitude[k])}
          >
            {drone ? <primitive object={drone} /> : <StandIn color={COLORS[p.firmware] ?? "#f4f4f2"} />}
          </group>
        );
      })}
      <gridHelper args={[60, 60, "#2c2c2a", "#1a1a19"]} />
    </group>
  );
}
