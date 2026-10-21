import { fireEvent, render, screen, within } from "@testing-library/react";

import type { SpecSheet } from "../data/types";
import { Spec } from "./Spec";

function combination(name: string, modules: string[], mass: number, hover: number) {
  return {
    name,
    modules,
    verdict: "pass",
    mass_g: mass,
    growth_margin_g: name === "mission" ? 200 : 0,
    cad_mass_g: mass - 50,
    center_of_gravity_mm: [0, 0, 0],
    checks: [
      { name: "Hover time", unit: "min", nominal: hover, pessimistic: hover - 4, limit: 21,
        higher_is_better: true, verdict: "pass", note: "" },
    ],
    top_speed_kmh: { full: 110, half: 105, reserve: 100 },
    least_power_speed_ms: 11.6,
    least_power_minutes: 43.3,
  };
}

const SPEC: SpecSheet = {
  schema_version: 1,
  sizing_case: "mission",
  verdict: "pass",
  targets: { reserve_fraction: 0.2 },
  combinations: [combination("base", [], 1860, 35.1), combination("mission", ["V", "P"], 2408, 25.8)],
  parts: [
    { role: "motor", module: null, id: "emax", maker: "Emax", model: "E3 2814", mass_g: 82, count: 4 },
  ],
};

function answering(body: unknown): typeof fetch {
  return (async () => ({ ok: true, json: async () => body })) as unknown as typeof fetch;
}

test("every combination's numbers show, and picking one switches to it", async () => {
  render(<Spec load={{ fromDisk: false, fetcher: answering(SPEC) }} />);
  expect(await screen.findByText("1860 g (with 0 g of margin)")).toBeInTheDocument();
  const base = screen.getByLabelText("base numbers");
  expect(within(base).getByText("35.1 min (31.1 pessimistic)")).toBeInTheDocument();
  fireEvent.click(screen.getByRole("tab", { name: "mission" }));
  expect(screen.getByText("2408 g (with 200 g of margin)")).toBeInTheDocument();
  const mission = screen.getByLabelText("mission numbers");
  expect(within(mission).getByText("25.8 min (21.8 pessimistic)")).toBeInTheDocument();
  expect(screen.getByRole("tab", { name: "mission" })).toHaveAttribute("aria-selected", "true");
});

test("the parts list says how many of each", async () => {
  render(<Spec load={{ fromDisk: false, fetcher: answering(SPEC) }} />);
  expect(await screen.findByText("Emax E3 2814")).toBeInTheDocument();
  expect(screen.getByText("4")).toBeInTheDocument();
});
