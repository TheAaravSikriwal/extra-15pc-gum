import type { TunnelFlow } from "../data/types";
import { AIR_GOES, tunnelFrame } from "./Flight";
import { SLOW_MOTION } from "./particles";

const flow = (direction: string, pitch = 0): TunnelFlow => ({
  schema_version: 1,
  name: `Max-${direction}`,
  direction,
  setup: "Max",
  speed: 10,
  color_max: 17,
  force_n: 2,
  pitch_deg: pitch,
  loop_s: 0.25,
  frames: 64,
  particles: { file: "p.bin", count: 1 },
  slice: { file: "s.bin", width: 1, height: 1, corners: [] },
});

test("in the tunnel the drone flies the other way to the air, at the particles' pace", () => {
  // nose first: the air goes aft, so it flies forward (east), 10 m/s slowed down
  const a = tunnelFrame(flow("front", 3.3), 1);
  const b = tunnelFrame(flow("front", 3.3), 2);
  expect(b.position[0] - a.position[0]).toBeCloseTo(10 / SLOW_MOTION);
  expect(b.position[1]).toBe(a.position[1]);
  // sideways to its right: the air goes to its left, so it flies south
  expect(tunnelFrame(flow("right"), 2).position[1]).toBeCloseTo(10 - (10 / SLOW_MOTION) * 2);
  // climbing, the ground doesn't move: the air alone shows that
  expect(tunnelFrame(flow("above"), 3).position.slice(0, 2)).toEqual([0, 0]);
  expect(AIR_GOES.above).toEqual([0, 0, -1]);
  // tilted the way it cruises, swaying a little, its props turning
  const q = tunnelFrame(flow("front", 3.3), 0).attitude;
  expect(2 * Math.asin(q[1])).toBeCloseTo((3.3 * Math.PI) / 180, 1);
  expect(a.motors.every((m) => m > 0)).toBe(true);
});
