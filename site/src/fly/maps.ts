// The run drawn small under the flying drone: its path seen from above, north up, at its real
// scale, and its height from liftoff to touchdown along the loop as it plays, so a long quiet
// stretch takes as little room as it takes time to watch and the moments have room.
import type { Playback } from "../data/types";
import type { Clip } from "./clip";

const LEAST_ACROSS_M = 10; // a run that barely moves still gets a 10 m square, so its drift reads true
const MOST_POINTS = 400; // plenty for a drawing a hundred pixels wide

export interface Plan {
  points: string; // an SVG polyline's, in a 100 by 100 square
  across: number; // m, the square's width
  place: (position: number[]) => [number, number];
}

export interface Profile {
  points: string; // in a 100 by 100 box stretched to fit, time across and height up
  top: number; // m, the highest it got above where it took off
  x: (t: number) => number; // where the run's time t plays in the loop, 0 to 100 across
  y: (height: number) => number; // m above the ground, 100 to 0 down the box
}

// the samples from liftoff to touchdown, thinned to a drawing's worth
function flown(p: Playback, clip: Clip): number[] {
  const all = p.t.map((t, k) => (t >= clip.start && t <= clip.end ? k : -1)).filter((k) => k >= 0);
  const every = Math.max(1, Math.ceil(all.length / MOST_POINTS));
  return all.filter((_, i) => i % every === 0 || i === all.length - 1);
}

const svgPoints = (xy: [number, number][]) => xy.map(([x, y]) => `${x.toFixed(1)},${y.toFixed(1)}`).join(" ");

export function planOf(p: Playback, clip: Clip): Plan {
  const ks = flown(p, clip);
  const east = ks.map((k) => p.position[k][0]);
  const north = ks.map((k) => p.position[k][1]);
  const mid = (v: number[]) => (Math.max(...v) + Math.min(...v)) / 2;
  const span = (v: number[]) => Math.max(...v) - Math.min(...v);
  const cx = mid(east);
  const cy = mid(north);
  const across = Math.max(LEAST_ACROSS_M, Math.max(span(east), span(north)) * 1.2);
  const place = (q: number[]): [number, number] => [50 + ((q[0] - cx) / across) * 100, 50 - ((q[1] - cy) / across) * 100];
  return { points: svgPoints(ks.map((k) => place(p.position[k]))), across, place };
}

export function profileOf(p: Playback, clip: Clip): Profile {
  // every sample there is, thinned evenly along the loop rather than the run, so the moments
  // that play at real time keep their detail
  const all = p.t.map((t, k) => (t >= clip.start && t <= clip.end ? k : -1)).filter((k) => k >= 0);
  const gap = clip.duration / MOST_POINTS;
  const ks: number[] = [];
  let was = -Infinity;
  for (const k of all) {
    const at = clip.timeOf(p.t[k]);
    if (at - was >= gap || k === all[all.length - 1]) {
      ks.push(k);
      was = at;
    }
  }
  const top = Math.max(1, ...ks.map((k) => p.position[k][2] - clip.ground));
  const x = (t: number) => Math.min(100, Math.max(0, (clip.timeOf(t) / (clip.duration || 1)) * 100));
  const y = (height: number) => 92 - (Math.max(0, height) / top) * 84;
  return { points: svgPoints(ks.map((k) => [x(p.t[k]), y(p.position[k][2] - clip.ground)])), top, x, y };
}

// a round number of meters for a label
export function roundMeters(m: number): string {
  return m < 20 ? m.toFixed(0) : String(Math.round(m / 5) * 5);
}
