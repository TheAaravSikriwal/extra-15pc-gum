// The wind tunnel's particles, as pcs14.aero.motion packs them, and where each one is at a moment
// of the loop: a dot where the particle is and a short tail back along where it's been, all of it
// fading in as the particle's released and out as it goes, so no air pops in or out. Air going
// the wind's own speed is drawn faint, so the air the drone disturbs stands out. The flow loops,
// so every particle's path repeats each loop exactly.
import { turbo } from "./turbo";

export const SLOW_MOTION = 20; // the air played this many times slower, so the eye can follow it
export const TRAIL = 4; // frames of tail behind each particle
export const FADE = 8; // frames to fade in after its release, and out before it goes
const DEEPER = 0.68; // turbo's bright middle, deeper, to read on white
const FAINT = 0.28; // how much of undisturbed air shows
const DISTURBED = 0.4; // this far off the wind's own speed (a share of it) is drawn in full

export interface ParticleSet {
  count: number;
  frames: number; // a loop's frames
  births: Uint16Array; // each one's release frame
  lengths: Uint16Array; // each one's points, a frame apart
  starts: Uint32Array; // each one's first point
  positions: Float32Array; // m, the drone's frame, three a point
  colors: Float32Array; // turbo by the air's speed there, three a point
  weights: Float32Array; // how strongly each point shows, by how far its air is off the wind's
}

// `colorMax` and `wind` in m/s; in still air (the hover) the fastest air shows strongest
export function decodeParticles(buffer: ArrayBuffer, colorMax = 17, wind = 0): ParticleSet {
  const [count, frames, points] = new Uint32Array(buffer, 0, 3);
  const births = new Uint16Array(buffer, 12, count);
  const lengths = new Uint16Array(buffer, 12 + count * 2, count);
  const mm = new Int16Array(buffer, 12 + count * 4, points * 3);
  const shares = new Uint8Array(buffer, 12 + count * 4 + points * 6, points);
  const starts = new Uint32Array(count);
  for (let i = 1; i < count; i++) starts[i] = starts[i - 1] + lengths[i - 1];
  const positions = new Float32Array(points * 3);
  for (let k = 0; k < points * 3; k++) positions[k] = mm[k] / 1000;
  const colors = new Float32Array(points * 3);
  const weights = new Float32Array(points);
  for (let k = 0; k < points; k++) {
    const share = shares[k] / 255;
    colors.set(turbo(share).map((v) => v * DEEPER), k * 3);
    const off = wind > 0 ? Math.abs(share * colorMax - wind) / (DISTURBED * wind) : (share * colorMax) / (0.5 * colorMax);
    weights[k] = FAINT + (1 - FAINT) * Math.min(1, off);
  }
  return { count, frames, births, lengths, starts, positions, colors, weights };
}

const smooth = (x: number) => {
  const t = Math.min(Math.max(x, 0), 1);
  return t * t * (3 - 2 * t);
};

// the vertices the tails take: TRAIL segments a particle, two ends each
export function trailVertices(set: ParticleSet): number {
  return set.count * TRAIL * 2;
}

// every particle at loop frame `frame` (fractional): its tail into `positions` (three a vertex)
// and `colors` (four a vertex, with alpha), each segment's ends where the particle was then, and
// its dot into `heads` and `headColors`, one a particle; all clear where a particle hasn't been
// released yet or has gone
export function trailsAt(
  set: ParticleSet,
  frame: number,
  positions: Float32Array,
  colors: Float32Array,
  heads?: Float32Array,
  headColors?: Float32Array,
): void {
  let v = 0;
  const point = (start: number, length: number, t: number, outPos: Float32Array, outCol: Float32Array, out: number): number => {
    const k = Math.min(Math.floor(t), length - 2);
    const f = t - k;
    const a = start + k;
    for (let c = 0; c < 3; c++) {
      outPos[out * 3 + c] = set.positions[a * 3 + c] * (1 - f) + set.positions[(a + 1) * 3 + c] * f;
      outCol[out * 4 + c] = set.colors[a * 3 + c] * (1 - f) + set.colors[(a + 1) * 3 + c] * f;
    }
    return set.weights[a] * (1 - f) + set.weights[a + 1] * f;
  };
  for (let i = 0; i < set.count; i++) {
    const length = set.lengths[i];
    const age = (((frame - set.births[i]) % set.frames) + set.frames) % set.frames;
    const alive = length >= 2 && age <= length - 1;
    const life = alive ? smooth(age / FADE) * smooth((length - 1 - age) / FADE) : 0;
    if (heads && headColors) {
      if (life > 0) headColors[i * 4 + 3] = life * point(set.starts[i], length, age, heads, headColors, i);
      else headColors[i * 4 + 3] = 0;
    }
    for (let s = 0; s < TRAIL; s++) {
      for (let end = 0; end < 2; end++) {
        const t = age - s - end;
        const out = v + end;
        if (life > 0 && t >= 0) {
          const weight = point(set.starts[i], length, t, positions, colors, out);
          colors[out * 4 + 3] = life * weight * (1 - (s + end) / TRAIL) * 0.8;
        } else {
          positions.fill(0, out * 3, out * 3 + 3);
          colors[out * 4 + 3] = 0;
        }
      }
      v += 2;
    }
  }
}

// the loop's frame for a moment of watching, in s
export function frameAt(seconds: number, loopS: number, frames: number): number {
  const played = seconds / SLOW_MOTION / loopS;
  return (played - Math.floor(played)) * frames;
}
