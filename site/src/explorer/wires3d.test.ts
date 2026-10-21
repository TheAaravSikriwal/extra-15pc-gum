import type { Wire3d } from "../data/types";
import { bundleSpread, visibleWires, wireColor, wirePoints } from "./wires3d";

function wire(path: number[][]): Wire3d {
  return {
    label: "a to b",
    harness: "h",
    ends: [
      { pin: "a.J1.1", at_mm: [0, 0, 0], piece: "a" },
      { pin: "b.J1.1", at_mm: [100, 0, 0], piece: "b" },
    ],
    route: path.length ? "r" : null,
    route_piece: path.length ? "wire r" : null,
    path_mm: path,
    awg: 26,
    diameter_mm: 1.1,
    wire: "silicone",
    role: "signal",
    length_mm: 100,
    gaps_mm: [],
  };
}

test("closed up, a wire runs from its pin through its route to its other pin, in meters", () => {
  const points = wirePoints(wire([[0, 10, 0], [100, 10, 0]]), () => [0, 0, 0]);
  expect(points).toEqual([
    [0, 0, 0],
    [0, 0.01, 0],
    [0.1, 0.01, 0],
    [0.1, 0, 0],
  ]);
});

test("pulled apart, each end moves with its piece and the route between blends the two", () => {
  const moved = (piece: string): [number, number, number] => (piece === "b" ? [0, 0, 0.2] : [0, 0, 0]);
  const points = wirePoints(wire([[50, 0, 0]]), moved);
  expect(points[0]).toEqual([0, 0, 0]); // a stays
  expect(points[2][2]).toBeCloseTo(0.2); // b went up 0.2 m
  expect(points[1][2]).toBeCloseTo(0.1); // halfway along, halfway up
});

test("the wires on one route lie side by side in their bundle, the ends still on their pins", () => {
  const a = { ...wire([[0, 0, 10], [100, 0, 10]]), label: "one" };
  const b = { ...wire([[0, 0, 10], [100, 0, 10]]), label: "two" };
  const alone = { ...wire([[0, 0, 10]]), label: "alone", route: "other" };
  const spread = bundleSpread([a, b, alone]);
  expect(spread.get("one")).not.toEqual(spread.get("two"));
  expect(spread.has("alone")).toBe(false);
  for (const s of spread.values()) {
    expect(s[0]).toBeCloseTo(0); // square to the route, which runs along x
    expect(Math.hypot(...s)).toBeLessThan(1.1 * Math.SQRT2); // inside the bundle
  }
  const points = wirePoints(a, () => [0, 0, 0], spread.get("one"));
  expect(points[0]).toEqual([0, 0, 0]); // the pin doesn't move
  expect(points[1]).not.toEqual([0, 0, 0.01]); // the route point does
});

test("a wire shows only when both of its ends' pieces do", () => {
  const w = wire([]);
  expect(visibleWires([w], new Set(["a", "b"]))).toHaveLength(1);
  expect(visibleWires([w], new Set(["a"]))).toHaveLength(0);
});

test("each kind of wire in its insulation's color", () => {
  expect(wireColor("power")).toBe("#c0302a");
  expect(wireColor("ground")).toBe("#1a1a1a");
  expect(wireColor("bus")).not.toBe(wireColor("signal"));
  expect(wireColor("power", "motors")).toBe("#1a1a1a"); // the motors' own black leads
});
