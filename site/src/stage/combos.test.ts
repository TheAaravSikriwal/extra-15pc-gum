import type { SpecSheet } from "../data/types";
import { statsFor } from "./combos";

const SPEC = {
  schema_version: 1,
  sizing_case: "x",
  verdict: "fail",
  targets: {},
  parts: [],
  combinations: [
    {
      name: "max",
      modules: ["V", "P", "C"],
      verdict: "fail",
      required: false,
      mass_g: 2620.4,
      growth_margin_g: 200,
      checks: [
        { name: "Hover time", unit: "min", nominal: 22.84, pessimistic: 19.71, higher_is_better: true, verdict: "pass", note: "", shown: "22.8 min" },
      ],
      top_speed_kmh: {},
      least_power_speed_ms: 8,
      least_power_minutes: 25,
      mass_lines: [],
      numbers: [],
    },
  ],
} as SpecSheet;

test("the readout for a combination: its weight, its hover both ways, and whether it meets its targets", () => {
  expect(statsFor(SPEC, "max")).toEqual({ mass: "2620 g", hover: "22.8 min", pessimistic: "19.7 min", verdict: "fail" });
  expect(statsFor(SPEC, "base")).toBeNull();
  expect(statsFor(null, "max")).toBeNull();
});
