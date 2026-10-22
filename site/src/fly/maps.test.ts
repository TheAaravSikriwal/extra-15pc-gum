import type { Playback } from "../data/types";
import { clipOf } from "./clip";
import { planOf, profileOf, roundMeters } from "./maps";

// a made-up run at 20 Hz: up to 20 m, 60 m north and back, and down
function outAndBack(): Playback {
  const t: number[] = [];
  const position: number[][] = [];
  for (let k = 0; k <= 80 * 20; k++) {
    const s = k / 20;
    const z = s < 2 ? 0 : s < 12 ? (s - 2) * 2 : s < 70 ? 20 : Math.max(0, 20 - (s - 70) * 2);
    const north = s < 12 ? 0 : s < 40 ? (s - 12) * (60 / 28) : s < 68 ? 60 - (s - 40) * (60 / 28) : 0;
    t.push(s);
    position.push([0, north, z]);
  }
  const level = t.map(() => [0, 0, 0, 1]);
  const motors = t.map(() => [560, 560, 560, 560]);
  return { schema_version: 1, scenario: "x", setup: "base", firmware: "mine", passed: true, findings: [], t, position, attitude: level, motors, events: [] };
}

test("from above, the path fills the square with north up, at its real scale", () => {
  const p = outAndBack();
  const plan = planOf(p, clipOf(p));
  expect(plan.across).toBeCloseTo(72, 0); // 60 m and a margin
  const [, home] = plan.place([0, 0, 0]);
  const [, far] = plan.place([0, 60, 0]);
  expect(far).toBeLessThan(home); // north is up the drawing
  expect(home - far).toBeCloseTo((60 / 72) * 100, 0);
  expect(plan.points.split(" ").length).toBeLessThanOrEqual(401);
});

test("a hover's square is at least 10 m, so a little drift looks little", () => {
  const p = outAndBack();
  p.position = p.position.map(([e, , z]) => [e, 0, z]);
  expect(planOf(p, clipOf(p)).across).toBe(10);
});

test("its height runs from liftoff on the left to touchdown on the right, the top at its highest", () => {
  const p = outAndBack();
  const clip = clipOf(p);
  const profile = profileOf(p, clip);
  expect(profile.top).toBeCloseTo(20, 0);
  expect(profile.x(clip.start)).toBe(0);
  expect(profile.x(clip.end)).toBe(100);
  expect(profile.y(20)).toBeLessThan(profile.y(0)); // higher is up
  // across is the loop as it plays: halfway along is halfway through watching it
  expect(profile.x(clip.at(clip.duration / 2).t)).toBeCloseTo(50, 0);
  expect(roundMeters(profile.top)).toBe("20");
  expect(roundMeters(73)).toBe("75");
});
