// Every wire on the model: each one pin to pin through its route, in the CAD's frame (meters, z
// up), the frame the model's pieces sit in. Pulled apart, each end moves with the piece it's on
// and the route's points between move with a blend of the two, by how far along the wire they are.
import type { Wire3d } from "../data/types";

export type Vec3 = [number, number, number];

const MM = 0.001;

// the wires sharing a route lie side by side in a bundle, not on top of each other: each one's
// route points shift (in mm) to its own spot around the bundle's middle, square to the route
export function bundleSpread(wires: Wire3d[]): Map<string, Vec3> {
  const byRoute = new Map<string, Wire3d[]>();
  for (const w of wires) if (w.route) byRoute.set(w.route, [...(byRoute.get(w.route) ?? []), w]);
  const out = new Map<string, Vec3>();
  for (const group of byRoute.values()) {
    if (group.length < 2) continue;
    const path = group[0].path_mm;
    const d = path.length > 1 ? path[path.length - 1].map((v, i) => v - path[0][i]) : [1, 0, 0];
    const along = normalize(d as Vec3);
    const u = normalize(Math.abs(along[2]) < 0.9 ? cross(along, [0, 0, 1]) : cross(along, [1, 0, 0]));
    const v = cross(along, u);
    const radius = (Math.max(...group.map((w) => w.diameter_mm)) * Math.sqrt(group.length)) / 2;
    group.forEach((w, k) => {
      const angle = (2 * Math.PI * k) / group.length;
      out.set(w.label, u.map((x, i) => radius * (Math.cos(angle) * x + Math.sin(angle) * v[i])) as Vec3);
    });
  }
  return out;
}

function cross(a: Vec3, b: Vec3): Vec3 {
  return [a[1] * b[2] - a[2] * b[1], a[2] * b[0] - a[0] * b[2], a[0] * b[1] - a[1] * b[0]];
}

function normalize(a: Vec3): Vec3 {
  const n = Math.hypot(...a) || 1;
  return a.map((x) => x / n) as Vec3;
}

export function wirePoints(wire: Wire3d, offset: (piece: string) => Vec3, spread: Vec3 = [0, 0, 0]): Vec3[] {
  const [a, b] = wire.ends;
  const inner = wire.path_mm.map((p) => p.map((v, i) => v + spread[i]));
  const raw = [a.at_mm, ...inner, b.at_mm];
  // how far along the wire each point is, from 0 at the first end to 1 at the other
  const along = [0];
  for (let k = 1; k < raw.length; k++) {
    along.push(along[k - 1] + Math.hypot(...raw[k].map((v, i) => v - raw[k - 1][i])));
  }
  const total = along[along.length - 1] || 1;
  const from = offset(a.piece);
  const to = offset(b.piece);
  return raw.map((p, k) => {
    const t = along[k] / total;
    return p.map((v, i) => v * MM + from[i] * (1 - t) + to[i] * t) as Vec3;
  });
}

export function visibleWires(wires: Wire3d[], shown: Set<string>): Wire3d[] {
  return wires.filter((w) => w.ends.every((e) => shown.has(e.piece)));
}

// red for power, black for ground, light gray for signal, yellow for the CAN bus; the motors'
// own leads are black whatever they carry
const ROLES: Record<string, string> = { power: "#c0302a", ground: "#1a1a1a", signal: "#cfccc3", bus: "#e6c229" };

export function wireColor(role: string, harness?: string): string {
  if (harness === "motors") return ROLES.ground;
  return ROLES[role] ?? ROLES.signal;
}
