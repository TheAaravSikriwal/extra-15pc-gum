// The combination the switched-on modules make, and its one line of numbers. Light on purpose:
// the stage's first paint needs them, and three.js isn't loaded yet then.
import type { SpecSheet } from "../data/types";

const MODULES = ["V", "P", "C"];

// the combination the modules switched on make
export function combinationFor(on: Set<string>): string {
  const names: Record<string, string> = {
    "": "base",
    V: "V",
    P: "P",
    C: "C",
    "V+P": "mission",
    "V+C": "V+C",
    "P+C": "P+C",
    "V+P+C": "max",
  };
  return names[MODULES.filter((m) => on.has(m)).join("+")];
}

export interface Stats {
  mass: string;
  hover: string;
  pessimistic: string | null;
  verdict: string; // against the combination's own targets
}

// the panel's readout for what the switched-on modules make
export function statsFor(spec: SpecSheet | null | undefined, combination: string): Stats | null {
  const c = spec?.combinations.find((x) => x.name === combination);
  if (!c) return null;
  const hover = c.checks.find((k) => k.name === "Hover time");
  return {
    mass: `${Math.round(c.mass_g)} g`,
    hover: hover ? `${hover.nominal.toFixed(1)} min` : "not worked out",
    pessimistic: hover?.pessimistic != null ? `${hover.pessimistic.toFixed(1)} min` : null,
    verdict: c.verdict,
  };
}

// one line of what the switched-on modules make: the weight, the hover time and the verdict
export function numbersFor(spec: SpecSheet | null | undefined, combination: string): string | null {
  const c = spec?.combinations.find((x) => x.name === combination);
  if (!c) return null;
  const hover = c.checks.find((k) => k.name === "Hover time");
  const time = hover
    ? `, hovers ${hover.nominal.toFixed(1)} min${hover.pessimistic != null ? ` (${hover.pessimistic.toFixed(1)} pessimistic)` : ""}`
    : "";
  return `${c.name}: ${Math.round(c.mass_g)} g${time}, ${c.verdict}`;
}

