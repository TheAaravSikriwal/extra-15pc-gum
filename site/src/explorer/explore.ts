// Exploring the wires: what's lit, what fades and what hides for whatever is picked, the
// harnesses to isolate, and where the camera flies for a picked wire.
import type { Wire3d } from "../data/types";
import type { Vec3 } from "./wires3d";

export type WireState = "normal" | "lit" | "dim" | "hidden";

export interface Picked {
  piece?: string | null; // a board: its own wires light up
  wire?: string | null; // one wire, by its label: only it lights up
  harness?: string | null; // one harness: the rest hide
}

export function wireStates(wires: Wire3d[], picked: Picked): Map<string, WireState> {
  return new Map(
    wires.map((w) => {
      if (picked.harness && w.harness !== picked.harness) return [w.label, "hidden"];
      if (picked.wire) return [w.label, w.label === picked.wire ? "lit" : "dim"];
      if (picked.piece) return [w.label, w.ends.some((e) => e.piece === picked.piece) ? "lit" : "dim"];
      return [w.label, "normal"];
    }),
  );
}

export function harnessesOf(wires: Wire3d[]): string[] {
  return [...new Set(wires.map((w) => w.harness))];
}

// a smooth start and a smooth stop, for the camera's glide
export function easeInOut(t: number): number {
  const x = Math.min(Math.max(t, 0), 1);
  return x < 0.5 ? 4 * x * x * x : 1 - (-2 * x + 2) ** 3 / 2;
}

// a wire's first pin in the model's frame (meters), moved with its piece when pulled apart
export function focusOf(wire: Wire3d, offset: (piece: string) => Vec3): Vec3 {
  const end = wire.ends[0];
  const moved = offset(end.piece);
  return end.at_mm.map((v, i) => Math.round((v * 0.001 + moved[i]) * 1e6) / 1e6) as Vec3;
}
