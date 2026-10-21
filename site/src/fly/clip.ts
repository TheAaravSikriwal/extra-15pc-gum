// A recorded run as a looping animation: from liftoff to touchdown, sped up into a 15 to 30
// second loop with the speed easing up and down, real time within 1.5 s of each of the run's
// own events (each kind once, at its first), and a calm hover at both ends so the loop joins
// up. A run that comes down hard, crashing or under its chute, plays to where it fell and
// fades out there, then fades back in at the start. Where a run's moments alone would overflow
// the loop, they play faster too, and the speed says so.
import type { Playback } from "../data/types";
import { isWindowMark } from "../flights/playback";

export type Quat = [number, number, number, number]; // x, y, z, w

export interface Frame {
  t: number; // the run's own time
  position: [number, number, number]; // m, east, north, up
  attitude: Quat;
  motors: number[]; // rad/s
  speed: number; // how many times real time
  fade: number; // 1 seen, 0 gone
}

export interface Clip {
  duration: number; // s, the loop
  start: number; // the run's time where it starts and ends
  end: number;
  fell: boolean; // came down hard (a crash, or under the chute) rather than landing
  at(s: number): Frame; // s into the loop
  timeOf(t: number): number; // where in the loop the run's time t plays
}

const AIRBORNE_M = 0.3;
const MOMENT_S = 1.5; // real time this close to an event
const RAMP_S = 1.0; // the least of the run's time the speed takes to change
const RAMP_LOOP_S = 0.6; // and about how long that takes to watch
const EASE_S = 0.8; // the hover at each end, in the loop's time
const FADE_S = 0.8;
const HARD_LANDING_MS = 2.5; // faster than this into the ground is a crash
const LOOP_MIN_S = 15;
const LOOP_MAX_S = 30;
const MOMENTS_SHARE = 0.75; // the most of the loop the moments take
const STEP_S = 0.05;

// the angle between the body's up and the world's
export function tilt(q: Quat | number[]): number {
  const [x, y] = q;
  const upZ = 1 - 2 * (x * x + y * y);
  return Math.acos(Math.min(1, Math.max(-1, upZ)));
}

// the same heading, level
function level(q: number[]): Quat {
  const [x, y, z, w] = q;
  const yaw = Math.atan2(2 * (w * z + x * y), 1 - 2 * (y * y + z * z));
  return [0, 0, Math.sin(yaw / 2), Math.cos(yaw / 2)];
}

function nlerp(a: number[], b: number[], f: number): Quat {
  const dot = a[0] * b[0] + a[1] * b[1] + a[2] * b[2] + a[3] * b[3];
  const s = dot < 0 ? -1 : 1;
  const q = a.map((v, i) => v * (1 - f) + s * b[i] * f);
  const n = Math.hypot(...q) || 1;
  return q.map((v) => v / n) as Quat;
}

function smooth(f: number): number {
  const x = Math.min(Math.max(f, 0), 1);
  return x * x * (3 - 2 * x);
}

function sampleAt(p: Playback, t: number) {
  const ts = p.t;
  let lo = 0;
  let hi = ts.length - 1;
  if (t <= ts[0]) hi = 0;
  else if (t >= ts[hi]) lo = hi;
  else {
    while (hi - lo > 1) {
      const mid = (lo + hi) >> 1;
      if (ts[mid] <= t) lo = mid;
      else hi = mid;
    }
  }
  const f = hi === lo ? 0 : (t - ts[lo]) / (ts[hi] - ts[lo]);
  const mix = (a: number[], b: number[]) => a.map((v, i) => v + (b[i] - v) * f);
  return {
    position: mix(p.position[lo], p.position[hi]) as [number, number, number],
    attitude: nlerp(p.attitude[lo], p.attitude[hi], f),
    motors: mix(p.motors[lo], p.motors[hi]),
  };
}

export function clipOf(p: Playback): Clip {
  const n = p.t.length;
  const ground = p.position[0][2];
  const first = Math.max(0, p.position.findIndex((q) => q[2] - ground > AIRBORNE_M));
  let last = n - 1;
  while (last > first && p.position[last][2] - p.position[n - 1][2] <= AIRBORNE_M) last--;
  // how it met the ground: fast or tumbled, and the clip runs on to where it fell
  const before = Math.max(last - 2, 0);
  const after = Math.min(last + 2, n - 1);
  const fall = (p.position[before][2] - p.position[after][2]) / (p.t[after] - p.t[before] || 1);
  const fell = fall > HARD_LANDING_MS || tilt(p.attitude[n - 1]) > Math.PI / 4;
  const start = p.t[first];
  const end = fell ? Math.min(p.t[n - 1], p.t[last] + 1.5) : p.t[Math.min(last + 1, n - 1)];
  const span = end - start;
  // the hover the loop joins at: the motors' speed at liftoff, level
  const hover = p.motors[Math.min(first + 10, n - 1)];

  // the run's key moments, each kind once (a flag raised over and over is one moment), and how
  // fast to play the rest
  const kinds = new Map<string, number>();
  for (const e of p.events) if (!isWindowMark(e.name) && !kinds.has(e.name)) kinds.set(e.name, e.at);
  const moments = [...kinds.values()].filter((at) => at >= start && at <= end);
  // the run's time in steps, and each step's distance from the nearest moment
  const steps: number[] = [];
  for (let t = start; t < end; t += STEP_S) steps.push(Math.min(STEP_S, end - t));
  const mids = steps.map((dt, k) => start + k * STEP_S + dt / 2);
  const nearest = mids.map((t) => Math.min(...moments.map((m) => Math.abs(t - m)), Infinity));
  // how much of a moment's speed each step takes, 1 at a moment to 0 away from one, easing over
  // about RAMP_LOOP_S of the loop: the faster the rest plays, the more of the run's time it takes
  const shares = (fast: number) => {
    const ramp = Math.max(RAMP_S, RAMP_LOOP_S * fast);
    return nearest.map((d) => 1 - smooth((d - MOMENT_S) / ramp));
  };
  // the speed blends on a log scale, so it changes evenly as it eases; the moments play at real
  // time unless they'd take more than MOMENTS_SHARE of the loop
  const moment = shares(1).reduce((sum, r, k) => sum + r * steps[k], 0); // the run's time at moments
  const target = Math.min(LOOP_MAX_S, Math.max(LOOP_MIN_S, span / 10, moment + 8));
  const speeds = (fast: number) => {
    const r = shares(fast);
    const atMoments = r.reduce((sum, v, k) => sum + v * steps[k], 0);
    const slow = Math.max(1, atMoments / (MOMENTS_SHARE * target));
    return r.map((v) => Math.exp((1 - v) * Math.log(fast) + v * Math.log(slow)));
  };
  const loopLength = (fast: number) => speeds(fast).reduce((sum, v, k) => sum + steps[k] / v, 0);
  let fast = 1;
  if (span > LOOP_MAX_S) {
    // the fast speed that makes the loop its length, found by halving
    let lo = 1;
    let hi = Math.max(2, span);
    for (let k = 0; k < 40; k++) {
      const mid = Math.sqrt(lo * hi);
      if (loopLength(mid) > target) lo = mid;
      else hi = mid;
    }
    fast = hi;
  }
  const speed = speeds(fast);
  const speedAt = (t: number) => speed[Math.min(Math.max(Math.floor((t - start) / STEP_S), 0), speed.length - 1)] ?? 1;

  // the loop's time for each step of the run's, for going either way
  const runT: number[] = [start];
  const loopT: number[] = [0];
  steps.forEach((dt, k) => {
    runT.push(runT[k] + dt);
    loopT.push(loopT[k] + dt / speed[k]);
  });
  const duration = loopT[loopT.length - 1];
  const lookup = (from: number[], to: number[], v: number) => {
    let lo = 0;
    let hi = from.length - 1;
    if (v <= from[0]) return to[0];
    if (v >= from[hi]) return to[hi];
    while (hi - lo > 1) {
      const mid = (lo + hi) >> 1;
      if (from[mid] <= v) lo = mid;
      else hi = mid;
    }
    return to[lo] + ((v - from[lo]) / (from[hi] - from[lo])) * (to[hi] - to[lo]);
  };

  return {
    duration,
    start,
    end,
    fell,
    timeOf: (t) => lookup(runT, loopT, t),
    at(s) {
      const loopS = Math.min(Math.max(s, 0), duration);
      const t = lookup(loopT, runT, loopS);
      const raw = sampleAt(p, t);
      // ease into the calm hover at the start, and out of it at the end unless it fell
      const intoStart = 1 - smooth(loopS / EASE_S);
      const intoEnd = fell ? 0 : smooth((loopS - (duration - EASE_S)) / EASE_S);
      const calm = Math.max(intoStart, intoEnd);
      const fade = fell ? Math.min(smooth(loopS / FADE_S), smooth((duration - loopS) / FADE_S)) : 1;
      return {
        t,
        position: raw.position,
        attitude: calm > 0 ? nlerp(raw.attitude, level(raw.attitude), calm) : raw.attitude,
        motors: raw.motors.map((m, i) => m + (hover[i] - m) * calm),
        speed: speedAt(t),
        fade,
      };
    },
  };
}
