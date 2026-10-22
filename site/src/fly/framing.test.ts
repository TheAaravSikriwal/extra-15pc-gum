import { FLY_ELEVATION_DEG, FLY_PULL, fitDistance, flyFraming } from "./framing";

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

test("once the drone's fit is known, the pull is from that, wherever the camera started", () => {
  const fitted = fitDistance(0.6, 35, 1.5, 1.25);
  expect(fitted).toBeCloseTo((1.25 * 0.6) / (2 * Math.tan((17.5 * Math.PI) / 180)), 5);
  expect(fitDistance(0.6, 35, 0.6, 1.25)).toBeCloseTo(fitted / 0.6, 5); // a tall screen fits the width
  const fly = flyFraming([3, 2, 4], [0, 0, 0], fitted);
  expect(Math.hypot(...fly.position)).toBeCloseTo(fitted * FLY_PULL, 5);
});
