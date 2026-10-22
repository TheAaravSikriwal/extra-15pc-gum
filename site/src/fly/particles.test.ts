import { decodeParticles, FADE, frameAt, SLOW_MOTION, TRAIL, trailsAt, trailVertices } from "./particles";
import { turbo } from "./turbo";

// two particles packed the way pcs14.aero.motion.particle_bytes packs them: the first released at
// frame 2 with 30 points marching 10 mm forward a frame, the second released at 60 with none
function packed(): ArrayBuffer {
  const points = 30;
  const buffer = new ArrayBuffer(12 + 2 * 4 + points * 6 + points);
  new Uint32Array(buffer, 0, 3).set([2, 64, points]);
  new Uint16Array(buffer, 12, 2).set([2, 60]);
  new Uint16Array(buffer, 16, 2).set([points, 0]);
  const mm = new Int16Array(buffer, 20, points * 3);
  for (let k = 0; k < points; k++) mm.set([k * 10, 0, 5], k * 3);
  new Uint8Array(buffer, 20 + points * 6, points).fill(150);
  return buffer;
}

test("the particles unpack into metres in the drone's frame, colored by their speed", () => {
  const set = decodeParticles(packed(), 17, 10);
  expect(set.count).toBe(2);
  expect(set.frames).toBe(64);
  expect(Array.from(set.positions.slice(3, 6))).toEqual([0.01, 0, 0.005].map(Math.fround));
  expect(set.colors[0]).toBeCloseTo(turbo(150 / 255)[0] * 0.68, 5);
  expect(Array.from(set.starts)).toEqual([0, 30]);
  // 150 of 255 of 17 m/s is the 10 m/s wind's own speed: undisturbed air, drawn faint
  expect(set.weights[0]).toBeLessThan(0.3);
  // in still air, the same speed is the downwash, drawn in full
  expect(decodeParticles(packed(), 17, 0).weights[0]).toBe(1);
});

test("a trail sits where the particle was, fading in from its release and out before it goes", () => {
  const set = decodeParticles(packed(), 17, 0);
  const positions = new Float32Array(trailVertices(set) * 3);
  const colors = new Float32Array(trailVertices(set) * 4);
  const heads = new Float32Array(set.count * 3);
  const headColors = new Float32Array(set.count * 4);
  // before its release, nothing of it shows
  trailsAt(set, 1, positions, colors);
  expect(Math.max(...colors.filter((_, k) => k % 4 === 3))).toBe(0);
  // ten and a half frames after it, its head is 105 mm along, and it's fully in
  trailsAt(set, 12.5, positions, colors, heads, headColors);
  expect(positions[0]).toBeCloseTo(0.105, 4);
  expect(colors[3]).toBeCloseTo(0.8, 5);
  expect(heads[0]).toBeCloseTo(0.105, 4); // its dot, at its head
  expect(headColors[3]).toBeCloseTo(1, 5);
  // its tail runs back a frame a segment, fading
  expect(positions[3]).toBeCloseTo(0.095, 4);
  expect(colors[4 * (TRAIL * 2 - 1) + 3]).toBeLessThan(colors[3]);
  // just after its release it's still coming in
  trailsAt(set, 2 + FADE / 2, positions, colors);
  expect(colors[3]).toBeGreaterThan(0);
  expect(colors[3]).toBeLessThan(1);
  // and once its points run out it's gone, as is the one with none
  trailsAt(set, 40, positions, colors);
  expect(Math.max(...colors.filter((_, k) => k % 4 === 3))).toBe(0);
});

test("the loop plays at a twentieth of the air's pace, and wraps", () => {
  const loop = 0.25;
  expect(frameAt(0, loop, 64)).toBe(0);
  expect(frameAt(loop * SLOW_MOTION * 0.5, loop, 64)).toBeCloseTo(32);
  expect(frameAt(loop * SLOW_MOTION * 1.25, loop, 64)).toBeCloseTo(16);
});
