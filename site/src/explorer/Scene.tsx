// The drone in 3D: the CAD's GLB, each piece in what it's made of, the modules switched on or
// off, pulled apart for the exploded view, and a click on a piece or a wire picking it.
import { type ThreeEvent, useFrame } from "@react-three/fiber";
import { useLayoutEffect, useMemo, useRef } from "react";
import * as THREE from "three";

import type { Piece, Route } from "../data/types";
import { exploded, heatColor, propSpin, shows, type Vec } from "./logic";
import { heatMaterial, lookFor, materialFor, planarUVs, SELECTED, TILE } from "./materials";

export interface SceneProps {
  root: THREE.Object3D; // the GLB's scene
  pieces: Map<string, Piece>;
  routes: Map<string, Route>; // by their GLB node
  modulesOn: Set<string>;
  explode: number; // 0 closed to 1 open
  selected: string | null;
  combination: string; // for the wires' heating
  kase: string;
  heat?: boolean; // the wires colored by their heating, or else in their insulation
  onSelect: (name: string | null) => void;
  spin?: number; // rad/s for the props, just for show; 0 holds them still
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
  // its middle and the drone's, in the frame its position is in: the CAD's GLB puts every
  // piece under a node that turns z-up into y-up, so the world's up is its parent's z
  middle: Vec;
  center: Vec;
  turns: number; // propSpin's
  meshes: THREE.Mesh[];
}

// a textured piece's meshes get texture coordinates, once, at the texture's size in the
// world: the GLB stores positions in its own small units under a scaled node
function giveUVs(meshes: THREE.Mesh[], tile: number) {
  const scale = new THREE.Vector3();
  for (const m of meshes) {
    if (m.geometry.getAttribute("uv")) continue;
    m.getWorldScale(scale);
    planarUVs(m.geometry, tile / (Math.abs(scale.x) || 1));
  }
}

export function DroneScene(p: SceneProps) {
  // each piece's node, where it started, its middle and its meshes, worked out once per model
  const homes = useMemo(() => {
    const byNode = new Map([...p.pieces.keys()].map((name) => [nodeName(name), name]));
    const found: Home[] = [];
    p.root.updateMatrixWorld(true);
    const whole = new THREE.Box3().setFromObject(p.root).getCenter(new THREE.Vector3());
    const local = (node: THREE.Object3D, v: THREE.Vector3): Vec => {
      const l = node.parent ? node.parent.worldToLocal(v.clone()) : v.clone();
      return [l.x, l.y, l.z];
    };
    p.root.traverse((node) => {
      const name = byNode.get(node.name);
      if (!name) return;
      const c = new THREE.Box3().setFromObject(node).getCenter(new THREE.Vector3());
      const meshes: THREE.Mesh[] = [];
      node.traverse((m) => {
        if (m instanceof THREE.Mesh) {
          m.castShadow = true;
          meshes.push(m);
        }
      });
      const look = lookFor(p.pieces.get(name) as Piece);
      if (look.texture) giveUVs(meshes, TILE[look.texture]);
      found.push({ name, node, position: node.position.clone(), middle: local(node, c),
                   center: local(node, whole), turns: propSpin(name), meshes });  // prettier-ignore
    });
    return { found, byNode };
  }, [p.root, p.pieces]);

  useLayoutEffect(() => {
    for (const { name, node, position, middle, center, meshes } of homes.found) {
      const piece = p.pieces.get(name) as Piece;
      node.visible = shows(piece, p.modulesOn);
      const [dx, dy, dz] = exploded(middle, center, p.explode);
      node.position.set(position.x + dx, position.y + dy, position.z + dz);
      const share = p.heat ? p.routes.get(name)?.heating_share[p.combination]?.[p.kase] : undefined;
      const material =
        name === p.selected ? SELECTED : share !== undefined ? heatMaterial(heatColor(share)) : materialFor(lookFor(piece));
      for (const m of meshes) m.material = material;
    }
  }, [homes, p.pieces, p.routes, p.modulesOn, p.explode, p.selected, p.combination, p.kase, p.heat]);

  // the props turning about their hubs, which is where the CAD puts each prop's node, about the
  // CAD's up (its z)
  const angle = useRef(0);
  useFrame((_, delta) => {
    if (!p.spin) return;
    angle.current += p.spin * delta;
    for (const h of homes.found) if (h.turns) h.node.rotation.z = h.turns * angle.current;
  });

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
