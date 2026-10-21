import { FLY_ELEVATION_DEG, FLY_PULL, flyFraming } from "./framing";

test("flying, the camera pulls back and comes down, looking the same way", () => {
  const inside = { position: [0.55, 0.4, 0.65] as [number, number, number], target: [0, 0.02, 0] as [number, number, number] };
  const fly = flyFraming(inside.position, inside.target);
  const away = (p: number[], t: number[]) => Math.hypot(...p.map((v, i) => v - t[i]));
  expect(away(fly.position, fly.target)).toBeCloseTo(away(inside.position, inside.target) * FLY_PULL, 5);
  const d = fly.position.map((v, i) => v - fly.target[i]);
  const elevation = (Math.atan2(d[1], Math.hypot(d[0], d[2])) * 180) / Math.PI;
  expect(elevation).toBeCloseTo(FLY_ELEVATION_DEG, 5);
  // the same heading: the horizontal direction doesn't turn
  expect(Math.atan2(d[2], d[0])).toBeCloseTo(Math.atan2(0.65, 0.55), 5);
  expect(fly.target).toEqual(inside.target);
});
