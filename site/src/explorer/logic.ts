// The 3D explorer's rules, apart from three.js so they test on their own: which pieces show,
// where the exploded view puts them, and how a wire is colored.
import type { Piece, Route } from "../data/types";

export type Vec = readonly [number, number, number];

// Base is always there; a module's pieces only while it's switched on
export function shows(piece: Piece, modulesOn: Set<string>): boolean {
  return piece.module === "base" || modulesOn.has(piece.module);
}

// how far the exploded view moves a piece whose middle is at `at`: straight out from the
// drone's middle, by `amount` (0 closed, 1 fully open) times twice its distance
export function exploded(at: Vec, center: Vec, amount: number): [number, number, number] {
  return [0, 1, 2].map((k) => (at[k] - center[k]) * 2 * amount) as [number, number, number];
}

// which way a prop turns, seen from above: +1 counterclockwise, -1 clockwise, 0 not a prop.
// PX4's quad X (pcs14.flight.generate.ORDER): front right and back left counterclockwise
export function propSpin(name: string): number {
  const m = /^prop (front|back) (left|right)$/.exec(name);
  if (!m) return 0;
  return (m[1] === "front") === (m[2] === "right") ? 1 : -1;
}

const MINT = [0x3d, 0xdc, 0x97];
const MAGENTA = [0xe6, 0x4f, 0xa0];

// a wire's color by its share of its heating limit: spearmint when cool, magenta at the limit
export function heatColor(share: number): string {
  const f = Math.min(Math.max(share, 0), 1);
  const mix = MINT.map((a, k) => Math.round(a + (MAGENTA[k] - a) * f));
  return `#${mix.map((v) => v.toString(16).padStart(2, "0")).join("")}`;
}

// each kind of piece in the style's colors: the structure dark, the parts lighter
export const KIND_COLORS: Record<string, string> = {
  frame: "#2c2c2a",
  motor: "#4a4a47",
  prop: "#b4b2a9",
  pack: "#3a3a37",
  bought: "#8c8a83",
  printed: "#f4f4f2",
  wire: "#3ddc97",
};

// a route's card: its wires end to end, and its hardest wire's share of the heating limit in
// one combination and case, or null where that wasn't worked out
export function wireRows(route: Route, combination: string, kase: string) {
  const share = route.heating_share[combination]?.[kase];
  return {
    share: share === undefined ? null : share,
    wires: route.wires.map((w) => ({ from: w.ends[0], to: w.ends[1] })),
  };
}
