// The drone in 3D: the CAD's GLB, each piece in what it's made of, the modules switched on or
// off, pulled apart for the exploded view, and a click on a piece or a wire picking it. Given
// every wire pin to pin, it draws each one in place of the CAD's bundled routes, stretching
// between its pieces as they pull apart.
import { Html } from "@react-three/drei";
import { type ThreeEvent, useFrame } from "@react-three/fiber";
import { useLayoutEffect, useMemo, useRef, useState } from "react";
import * as THREE from "three";

import type { Piece, Route, Wire3d } from "../data/types";
import { exploded, heatColor, propSpin, shows, type Vec } from "./logic";
import { focusOf, wireStates } from "./explore";
import {
  SUBPART_NAMES,
  dimWireMaterial,
  ghostMaterial,
  heatMaterial,
  LIT_WIRE,
  lookFor,
  materialFor,
  planarUVs,
  SELECTED,
  TILE,
  wireMaterial,
} from "./materials";
import { bundleSpread, type Vec3, visibleWires, wireColor, wirePoints } from "./wires3d";

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
  // each prop's own rad/s by its piece's name, written every frame by a flight: overrides spin
  spins?: { current: Record<string, number> | null };
  wires?: Wire3d[]; // every wire pin to pin, drawn in place of the bundled routes
  light?: boolean; // each wire a thin line, for phones
  pickedWire?: string | null; // a wire picked by its label: it lights up and the rest fade
  harness?: string | null; // one harness isolated: the rest hide
  onPickWire?: (label: string | null) => void;
  onFocus?: (at: Vec3 | null) => void; // a picked wire's first pin in the world, for the camera
}

interface PinLabel {
  key: string;
  at: Vec3; // in the world
  text: string;
}

// each wire as a tube at its own thickness, or a line when light
function wireObject(points: Vec3[], radius: number, material: THREE.Material, light: boolean): THREE.Object3D {
  const vectors = points.map((p) => new THREE.Vector3(...p));
  if (light) {
    return new THREE.Line(new THREE.BufferGeometry().setFromPoints(vectors), material);
  }
  const path = new THREE.CurvePath<THREE.Vector3>();
  for (let k = 1; k < vectors.length; k++) path.add(new THREE.LineCurve3(vectors[k - 1], vectors[k]));
  return new THREE.Mesh(new THREE.TubeGeometry(path, Math.max(8, vectors.length * 6), radius, 6, false), material);
}

const LINES = new Map<string, THREE.LineBasicMaterial>();
function lineMaterial(color: string, dim = false): THREE.LineBasicMaterial {
  const key = `${color}${dim ? " dim" : ""}`;
  let m = LINES.get(key);
  if (!m) {
    m = new THREE.LineBasicMaterial({ color, transparent: dim, opacity: dim ? 0.15 : 1 });
    LINES.set(key, m);
  }
  return m;
}

const MINT = "#3ddc97";

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
  parts: (string | null)[]; // each mesh's named part of the look (chips, plugs...), if any
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
      const parts: (string | null)[] = [];
      // a mesh's named part of the look: the nearest node between it and the piece with one.
      // GLTFLoader makes repeated names unique ("pins", then "pins_1"), so the number goes
      const partOf = (m: THREE.Object3D): string | null => {
        for (let o: THREE.Object3D | null = m; o && o !== node; o = o.parent) {
          const name = o.name.replace(/_\d+$/, "");
          if (SUBPART_NAMES.has(name)) return name;
        }
        return null;
      };
      node.traverse((m) => {
        if (m instanceof THREE.Mesh) {
          m.castShadow = true;
          meshes.push(m);
          parts.push(partOf(m));
        }
      });
      const look = lookFor(p.pieces.get(name) as Piece);
      // the texture goes on the piece itself or its board, not on the chips and pins
      if (look.texture) giveUVs(meshes.filter((_, k) => parts[k] === null || parts[k] === "board"), TILE[look.texture]);
      found.push({ name, node, position: node.position.clone(), middle: local(node, c),
                   center: local(node, whole), turns: propSpin(name), meshes, parts });  // prettier-ignore
    });
    return { found, byNode };
  }, [p.root, p.pieces]);

  // the pieces a picked wire joins
  const ends = useMemo(() => {
    const w = p.pickedWire ? p.wires?.find((x) => x.label === p.pickedWire) : undefined;
    return w ? new Set(w.ends.map((e) => e.piece)) : null;
  }, [p.pickedWire, p.wires]);

  useLayoutEffect(() => {
    for (const { name, node, position, middle, center, meshes, parts } of homes.found) {
      const piece = p.pieces.get(name) as Piece;
      node.visible = shows(piece, p.modulesOn);
      const [dx, dy, dz] = exploded(middle, center, p.explode);
      node.position.set(position.x + dx, position.y + dy, position.z + dz);
      const share = p.heat ? p.routes.get(name)?.heating_share[p.combination]?.[p.kase] : undefined;
      // with a wire picked, every piece but the two it joins fades to a ghost, so a close-up of
      // its pins can't end up behind something
      const ghost = ends !== null && !ends.has(name);
      const material = ghost
        ? ghostMaterial(lookFor(piece))
        : name === p.selected
          ? SELECTED
          : share !== undefined
            ? heatMaterial(heatColor(share))
            : materialFor(lookFor(piece));
      meshes.forEach((m, k) => {
        // a look's chips, plugs and pins take their own materials, unless the whole piece is lit
        const own = parts[k] && !ghost && material !== SELECTED && share === undefined;
        m.material = own ? materialFor(lookFor(piece, parts[k])) : ghost && parts[k] ? ghostMaterial(lookFor(piece, parts[k])) : material;
      });
      // the bundled routes give way to the wires drawn one by one
      if (p.wires && piece.kind === "wire") node.visible = false;
    }
  }, [homes, p.pieces, p.routes, p.modulesOn, p.explode, p.selected, p.combination, p.kase, p.heat, p.wires, ends]);

  // every wire, rebuilt as the drone pulls apart, under the pieces' own parent; lit, faded or
  // hidden for whatever's picked, with the picked pins labeled
  const wireGroup = useMemo(() => new THREE.Group(), []);
  const [labels, setLabels] = useState<PinLabel[]>([]);
  const focus = useRef(p.onFocus);
  focus.current = p.onFocus;
  useLayoutEffect(() => {
    const parent = homes.found[0]?.node.parent;
    if (!parent || !p.wires) return;
    wireGroup.name = "wires3d";
    parent.add(wireGroup);
    const offsets = new Map<string, Vec3>();
    const shown = new Set<string>();
    for (const { name, middle, center } of homes.found) {
      offsets.set(name, exploded(middle, center, p.explode) as Vec3);
      if (shows(p.pieces.get(name) as Piece, p.modulesOn)) shown.add(name);
    }
    const offset = (piece: string) => offsets.get(piece) ?? ([0, 0, 0] as Vec3);
    const world = (v: Vec3): Vec3 => parent.localToWorld(new THREE.Vector3(...v)).toArray() as Vec3;
    const visible = visibleWires(p.wires, shown);
    const states = wireStates(visible, { piece: p.selected, wire: p.pickedWire, harness: p.harness });
    const spread = bundleSpread(p.wires);
    const pinLabels: PinLabel[] = [];
    for (const w of visible) {
      const state = states.get(w.label) ?? "normal";
      if (state === "hidden") continue;
      const share = p.heat && w.route_piece ? p.routes.get(w.route_piece)?.heating_share[p.combination]?.[p.kase] : undefined;
      const color = state === "lit" ? MINT : share !== undefined ? heatColor(share) : wireColor(w.role, w.harness);
      const material = p.light
        ? lineMaterial(color, state === "dim")
        : state === "lit"
          ? LIT_WIRE
          : state === "dim"
            ? dimWireMaterial(color)
            : share !== undefined
              ? heatMaterial(color)
              : wireMaterial(color);
      const points = wirePoints(w, offset, spread.get(w.label));
      // a lit wire a little thicker, so it stands out of its bundle
      const radius = (w.diameter_mm / 2) * 0.001 * (state === "lit" ? 1.8 : 1);
      const object = wireObject(points, radius, material, !!p.light);
      object.userData.wire = w.label;
      wireGroup.add(object);
      if (state === "lit") {
        // the picked wire's two pins, or the picked board's own
        [w.ends[0], w.ends[1]].forEach((e, k) => {
          if (!p.pickedWire && e.piece !== p.selected) return;
          const at = k === 0 ? points[0] : points[points.length - 1];
          pinLabels.push({ key: `${w.label} ${k}`, at: world(at), text: e.pin.split(".").slice(1).join(" ") });
        });
      }
    }
    // a board's pins can carry several wires: one label each
    const seen = new Set<string>();
    setLabels(pinLabels.filter((l) => !seen.has(l.text + l.at.join()) && seen.add(l.text + l.at.join())));
    const picked = p.pickedWire ? p.wires.find((w) => w.label === p.pickedWire) : undefined;
    focus.current?.(picked ? world(focusOf(picked, offset)) : null);
    return () => {
      for (const child of [...wireGroup.children]) {
        if (child instanceof THREE.Mesh || child instanceof THREE.Line) child.geometry.dispose();
        wireGroup.remove(child);
      }
      parent.remove(wireGroup);
    };
  }, [homes, wireGroup, p.wires, p.light, p.pieces, p.routes, p.modulesOn, p.explode, p.combination, p.kase, p.heat,
      p.selected, p.pickedWire, p.harness]);  // prettier-ignore

  // the props turning about their hubs, which is where the CAD puts each prop's node, about the
  // CAD's up (its z)
  const angle = useRef(0);
  const angles = useRef(new Map<string, number>());
  useFrame((_, delta) => {
    const own = p.spins?.current;
    if (own) {
      for (const h of homes.found) {
        if (!h.turns) continue;
        const a = (angles.current.get(h.name) ?? 0) + (own[h.name] ?? 0) * delta;
        angles.current.set(h.name, a);
        h.node.rotation.z = h.turns * a;
      }
      return;
    }
    if (!p.spin) return;
    angle.current += p.spin * delta;
    for (const h of homes.found) if (h.turns) h.node.rotation.z = h.turns * angle.current;
  });

  return (
    <>
      <primitive
        object={p.root}
        onClick={(e: ThreeEvent<MouseEvent>) => {
          e.stopPropagation();
          const wire = e.object.userData.wire as string | undefined;
          if (wire && p.onPickWire) p.onPickWire(wire);
          else p.onSelect(pieceOf(e.object, homes.byNode));
        }}
        onPointerMissed={() => {
          p.onSelect(null);
          p.onPickWire?.(null);
        }}
      />
      {labels.map((l) => (
        <Html key={l.key} position={l.at} center zIndexRange={[20, 0]}>
          <span className="pin-label">{l.text}</span>
        </Html>
      ))}
    </>
  );
}
