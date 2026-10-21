import type { Playback } from "../data/types";
import { clipOf, tilt } from "./clip";

const HOVER = 560;

// a made-up run at 20 Hz: on the ground, up to 10 m, a long hold with a sharp roll at `rollAt`,
// then down; or, crashing, falling from the hold and hitting the ground hard, tumbled
function run(seconds: number, opts: { rollAt?: number; crash?: boolean } = {}): Playback {
  const t: number[] = [];
  const position: number[][] = [];
  const attitude: number[][] = [];
  const motors: number[][] = [];
  const up = 5;
  const down = opts.crash ? seconds - 2 : seconds - 8;
  for (let k = 0; k <= seconds * 20; k++) {
    const s = k / 20;
    let z = s < up ? 0 : Math.min(10, (s - up) * 2);
    if (s > down) z = opts.crash ? Math.max(0, 10 - 4.9 * (s - down) ** 2) : Math.max(0, 10 - (s - down) * 2);
    const rolling = opts.rollAt !== undefined && Math.abs(s - opts.rollAt) < 1;
    const tumbled = opts.crash && z === 0 && s > down;
    const roll = tumbled ? 1.6 : rolling ? 0.3 : 0;
    t.push(s);
    position.push([0.1 * s, 0, z]);
    attitude.push([Math.sin(roll / 2), 0, 0, Math.cos(roll / 2)]);
    const flying = z > 0 || (s >= up && s <= down);
    motors.push(flying && !tumbled ? [HOVER, HOVER, HOVER, HOVER] : [0, 0, 0, 0]);
  }
  const events = [
    { at: 4.5, name: "armed" },
    ...(opts.rollAt !== undefined ? [{ at: opts.rollAt, name: "step" }] : []),
    { at: 40, name: "hold start" }, // a grader's window mark, not a moment
  ];
  return { schema_version: 1, scenario: "x", setup: "base", firmware: "mine", passed: true, findings: [], t, position, attitude, motors, events };
}

test("a long run loops in 15 to 30 seconds, sped up", () => {
  const clip = clipOf(run(300, { rollAt: 150 }));
  expect(clip.duration).toBeGreaterThanOrEqual(15);
  expect(clip.duration).toBeLessThanOrEqual(30);
  expect(clip.at(clip.duration * 0.25).speed).toBeGreaterThan(5);
});

test("a short run plays at real time, liftoff to touchdown", () => {
  const clip = clipOf(run(25));
  expect(clip.at(3).speed).toBeCloseTo(1);
  expect(clip.start).toBeGreaterThan(4.9); // from liftoff, not the time on the ground
  expect(clip.end).toBeLessThan(25);
  expect(clip.duration).toBeCloseTo(clip.end - clip.start, 1);
});

test("a key moment plays at real time, and the speed eases in and out of it", () => {
  const clip = clipOf(run(300, { rollAt: 150 }));
  const at = clip.timeOf(150);
  expect(clip.at(at).speed).toBeCloseTo(1);
  expect(clip.at(at).attitude[0]).toBeGreaterThan(0.1); // the roll itself is there
  // the grader's "hold start" mark isn't a moment
  expect(clip.at(clip.timeOf(40)).speed).toBeGreaterThan(1);
  // no jumps in speed: neighbors a tenth of a second apart differ by a little
  for (let s = 0; s < clip.duration - 0.1; s += 0.1) {
    expect(Math.abs(clip.at(s + 0.1).speed - clip.at(s).speed)).toBeLessThan(clip.at(s).speed * 0.6 + 1);
  }
});

test("a flag raised over and over is one moment, and too many moments play faster too", () => {
  const busy = run(600, { rollAt: 150 });
  // a battery warning every 4 s for the rest of the run, and forty different events besides
  for (let at = 160; at < 590; at += 4) busy.events.push({ at, name: "battery warning" });
  for (let k = 0; k < 40; k++) busy.events.push({ at: 170 + k * 10, name: `event ${k}` });
  busy.events.sort((a, b) => a.at - b.at);
  const clip = clipOf(busy);
  expect(clip.duration).toBeLessThanOrEqual(30.5);
  expect(clip.at(clip.timeOf(170)).speed).toBeGreaterThan(1); // a moment, but sped up to fit
});

test("the loop starts and ends in a calm hover, so it joins up", () => {
  const clip = clipOf(run(300, { rollAt: 150 }));
  for (const frame of [clip.at(0), clip.at(clip.duration)]) {
    expect(tilt(frame.attitude)).toBeLessThan(0.02);
    expect(frame.motors.every((m) => Math.abs(m - HOVER) < 1)).toBe(true);
    expect(frame.fade).toBe(1);
  }
});

test("a crash doesn't ease back to a hover: it fades out where it ended, and back in", () => {
  const clip = clipOf(run(120, { crash: true }));
  expect(clip.fell).toBe(true);
  expect(clipOf(run(120)).fell).toBe(false);
  const last = clip.at(clip.duration);
  expect(last.fade).toBeCloseTo(0);
  expect(tilt(last.attitude)).toBeGreaterThan(1); // still lying where it fell
  expect(clip.at(0).fade).toBeCloseTo(0);
  expect(clip.at(clip.duration / 2).fade).toBe(1);
});
