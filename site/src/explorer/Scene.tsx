// The drone in 3D: the CAD's GLB, its pieces colored by kind, the modules switched on or off,
// pulled apart for the exploded view, and a click on a piece or a wire picking it.
import type { ThreeEvent } from "@react-three/fiber";
import { useLayoutEffect, useMemo } from "react";
import * as THREE from "three";

import type { Piece, Route } from "../data/types";
import { exploded, heatColor, KIND_COLORS, shows, type Vec } from "./logic";

export interface SceneProps {
  root: THREE.Object3D; // the GLB's scene
  pieces: Map<string, Piece>;
  routes: Map<string, Route>; // by their GLB node
  modulesOn: Set<string>;
  explode: number; // 0 closed to 1 open
  selected: string | null;
  combination: string; // for the wires' colors
  kase: string;
  onSelect: (name: string | null) => void;
}

// the name three.js gives a piece's node: its GLTFLoader cleans names on the way in, so
// "wire battery leads" arrives as "wire_battery_leads"
export function nodeName(piece: string): string {
  return THREE.PropertyBinding.sanitizeNodeName(piece);
}

// the piece a clicked mesh belongs to (the mesh itself or its nearest named parent), by the
// piece's own name
export function pieceOf(object: THREE.Object3D | null, byNode: Map<string, string>): string | null {
  for (let o = object; o; o = o.parent) {
    const name = byNode.get(o.name);
    if (name) return name;
  }
  return null;
}

interface Home {
  name: string; // the piece's own
  node: THREE.Object3D;
  position: THREE.Vector3; // where the CAD put it
  middle: Vec; // its middle, in the model's frame
}

export function DroneScene(p: SceneProps) {
  // each piece's node, where it started, and its middle, worked out once per model
  const homes = useMemo(() => {
    const byNode = new Map([...p.pieces.keys()].map((name) => [nodeName(name), name]));
    const found: Home[] = [];
    p.root.updateMatrixWorld(true);
    p.root.traverse((node) => {
      const name = byNode.get(node.name);
      if (!name) return;
      const box = new THREE.Box3().setFromObject(node);
      const c = box.getCenter(new THREE.Vector3());
      found.push({ name, node, position: node.position.clone(), middle: [c.x, c.y, c.z] });
    });
    const whole = new THREE.Box3().setFromObject(p.root).getCenter(new THREE.Vector3());
    return { found, byNode, center: [whole.x, whole.y, whole.z] as Vec };
  }, [p.root, p.pieces]);

  useLayoutEffect(() => {
    for (const { name, node, position, middle } of homes.found) {
      const piece = p.pieces.get(name) as Piece;
      node.visible = shows(piece, p.modulesOn);
      const [dx, dy, dz] = exploded(middle, homes.center, p.explode);
      node.position.set(position.x + dx, position.y + dy, position.z + dz);
      const route = p.routes.get(name);
      const share = route?.heating_share[p.combination]?.[p.kase];
      const color =
        name === p.selected
          ? "#3ddc97"
          : route && share !== undefined
            ? heatColor(share)
            : (KIND_COLORS[piece.kind] ?? "#8c8a83");
      node.traverse((m) => {
        if (m instanceof THREE.Mesh) {
          m.material = new THREE.MeshStandardMaterial({
            color,
            metalness: 0.1,
            roughness: 0.7,
            emissive: name === p.selected ? "#123d2a" : "#000000",
          });
        }
      });
    }
  }, [homes, p.pieces, p.routes, p.modulesOn, p.explode, p.selected, p.combination, p.kase]);

  return (
    <primitive
      object={p.root}
      onClick={(e: ThreeEvent<MouseEvent>) => {
        e.stopPropagation();
        p.onSelect(pieceOf(e.object, homes.byNode));
      }}
      onPointerMissed={() => p.onSelect(null)}
    />
  );
}
