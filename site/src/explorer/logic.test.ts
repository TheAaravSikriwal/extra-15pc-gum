import type { Piece, Route } from "../data/types";
import { exploded, heatColor, KIND_COLORS, shows, wireRows } from "./logic";

function piece(name: string, module: string, kind = "bought"): Piece {
  return { name, kind, module, mass_g: 1, part_id: null, moving: false, catalog: null };
}

test("Base always shows; a module's pieces only while it's switched on", () => {
  const on = new Set(["V"]);
  expect(shows(piece("frame", "base", "frame"), on)).toBe(true);
  expect(shows(piece("ark-gps", "V"), on)).toBe(true);
  expect(shows(piece("chute", "P"), on)).toBe(false);
});

test("the exploded view pushes each piece out from the middle, more as it opens", () => {
  const center = [0, 0, 0] as const;
  expect(exploded([0.1, 0, 0], center, 0)).toEqual([0, 0, 0]);
  const half = exploded([0.1, 0, 0], center, 0.5);
  const full = exploded([0.1, 0, 0], center, 1);
  expect(half[0]).toBeGreaterThan(0);
  expect(full[0]).toBeCloseTo(2 * half[0]);
  expect(exploded([0, 0, -0.05], center, 1)[2]).toBeLessThan(0); // down stays down
  expect(exploded([0, 0, 0], center, 1)).toEqual([0, 0, 0]); // the middle stays put
});

test("a wire's color goes from spearmint to magenta as it nears its heating limit", () => {
  expect(heatColor(0)).toBe("#3ddc97");
  expect(heatColor(1)).toBe("#e64fa0");
  expect(heatColor(2)).toBe("#e64fa0"); // past the limit is still the limit's color
  expect(heatColor(0.5)).not.toBe(heatColor(0));
});

test("every kind of piece has a color from the style", () => {
  for (const kind of ["frame", "motor", "prop", "pack", "bought", "printed", "wire"]) {
    expect(KIND_COLORS[kind]).toMatch(/^#[0-9a-f]{6}$/);
  }
});

test("a route lists its wires with both ends, and how hard it works in a case", () => {
  const route: Route = {
    name: "battery leads",
    node: "wire battery leads",
    wires: [{ label: "lead.XT60.+ to esc.BAT.VBAT", ends: ["lead.XT60.+", "esc.BAT.VBAT"] }],
    heating_share: { max: { hover: 0.17, burst: 0.31 } },
  };
  expect(wireRows(route, "max", "burst")).toEqual({
    share: 0.31,
    wires: [{ from: "lead.XT60.+", to: "esc.BAT.VBAT" }],
  });
  expect(wireRows(route, "base", "burst").share).toBeNull(); // not worked out for that one
});
