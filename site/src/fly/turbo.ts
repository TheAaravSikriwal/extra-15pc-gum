// Turbo, the project's colors for anything continuous from CFD (docs/style.md): matplotlib's
// turbo map sampled at thirteen even stops, blended in between. Blue is slow, red is fast.
const STOPS = [
  "#30123b", "#434eba", "#4685fa", "#28bceb", "#1ae4b6", "#55fa76", "#a4fc3c",
  "#d9e436", "#faba39", "#fb7e21", "#e4450a", "#b91e02", "#7a0403",
].map((hex) => [1, 3, 5].map((i) => parseInt(hex.slice(i, i + 2), 16) / 255)); // prettier-ignore

// f from 0 to 1, as red, green and blue from 0 to 1
export function turbo(f: number): [number, number, number] {
  const x = Math.min(Math.max(Number.isFinite(f) ? f : 0, 0), 1) * (STOPS.length - 1);
  const k = Math.min(Math.floor(x), STOPS.length - 2);
  const t = x - k;
  return STOPS[k].map((v, i) => v + (STOPS[k + 1][i] - v) * t) as [number, number, number];
}

export function turboCss(f: number): string {
  const [r, g, b] = turbo(f).map((v) => Math.round(v * 255));
  return `rgb(${r}, ${g}, ${b})`;
}

// a CSS gradient across the whole map, for a legend
export const TURBO_GRADIENT = `linear-gradient(to right, ${STOPS.map((_, k) => turboCss(k / (STOPS.length - 1))).join(", ")})`;
