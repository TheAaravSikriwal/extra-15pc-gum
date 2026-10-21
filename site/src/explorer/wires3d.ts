// Every wire on the model: each one pin to pin through its route, in the CAD's frame (meters, z
// up), the frame the model's pieces sit in. Pulled apart, each end moves with the piece it's on
// and the route's points between move with a blend of the two, by how far along the wire they are.
import type { Wire3d } from "../data/types";

export type Vec3 = [number, number, number];

const MM = 0.001;

export function wirePoints(wire: Wire3d, offset: (piece: string) => Vec3): Vec3[] {
  const [a, b] = wire.ends;
  const raw = [a.at_mm, ...wire.path_mm, b.at_mm];
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
