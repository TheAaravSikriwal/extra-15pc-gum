// Playing a flight back: which logged sample goes with the clock's moment, the events so far,
// the charts' series, and the step from the log's east-north-up into three.js's y-up.
import type { Cell } from "../charts/Matrix";
import type { FlightEvent, Flights, Playback } from "../data/types";
import type { Chapter } from "../play/clock";

// the last sample at or before `t`
export function indexAt(p: Playback, t: number): number {
  let lo = 0;
  let hi = p.t.length - 1;
  if (t <= p.t[0]) return 0;
  if (t >= p.t[hi]) return hi;
  while (hi - lo > 1) {
    const mid = (lo + hi) >> 1;
    if (p.t[mid] <= t) lo = mid;
    else hi = mid;
  }
  return lo;
}

export function eventsSoFar(p: Playback, t: number): FlightEvent[] {
  return p.events.filter((e) => e.at <= t);
}

export function duration(runs: Playback[]): number {
  return Math.max(0, ...runs.map((p) => p.t[p.t.length - 1] ?? 0));
}

const LABELS: Record<string, string> = { px4: "PX4", mine: "mine" };

// a grader's window marks ("hold start", "before end"), which the event lists show but the
// chapters leave out: the chapters are for what happened
export function isWindowMark(name: string): boolean {
  return / (start|end)$/.test(name);
}

// both runs' events as the clock's chapters, each saying whose it is, and each once a run: a
// failure detector that raises its flag over and over gets one chapter, at the first
export function chapters(runs: Playback[]): Chapter[] {
  return runs.flatMap((p) => {
    const seen = new Set<string>();
    return p.events
      .filter((e) => !isWindowMark(e.name) && !seen.has(e.name) && seen.add(e.name))
      .map((e) => ({ at: Math.max(0, e.at), name: `${LABELS[p.firmware] ?? p.firmware}: ${e.name}` }));
  });
}

// east, north, up into three.js's x right, y up, z toward the viewer
export function toThree([east, north, up]: number[]): [number, number, number] {
  return [east, up, -north];
}

export function series(p: Playback) {
  const height = p.position.map((x) => x[2]);
  const speed = p.position.map((x, k) => {
    if (k === 0) return 0;
    const dt = p.t[k] - p.t[k - 1] || 1;
    const prev = p.position[k - 1];
    return Math.hypot(x[0] - prev[0], x[1] - prev[1]) / dt;
  });
  const motors = p.motors.map((m) => m.reduce((a, b) => a + b, 0) / m.length);
  return { height, speed, motors };
}

export function cellFor(f: Flights, firmware: string, scenario: string, setup: string): Cell {
  const r = f.runs.find((x) => x.firmware === firmware && x.scenario === scenario && x.setup === setup);
  if (!r || !r.flown) return "not yet";
  return r.passed ? "pass" : "fail";
}
