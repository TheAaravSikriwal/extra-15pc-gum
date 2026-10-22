import { fireEvent, render, screen, within } from "@testing-library/react";

import type { SpecSheet } from "../data/types";
import { Spec } from "./Spec";

function combination(name: string, modules: string[], mass: number, hover: string) {
  return {
    name,
    modules,
    verdict: "pass",
    required: name === "mission",
    mass_g: mass,
    growth_margin_g: name === "mission" ? 200 : 0,
    cad_mass_g: mass - 50,
    center_of_gravity_mm: [0.1, 0, 4.3],
    checks: [
      {
        name: "Hover time", unit: "min", nominal: 25.89, pessimistic: 22.27, limit: 21, higher_is_better: true,
        verdict: "pass", note: "", shown: `${hover} min`, shown_pessimistic: "22.2 min", shown_limit: "at least 21.0 min",
        shown_margin: "+23%",
      },
      {
        name: "Full-throttle current", unit: "A", nominal: 90, pessimistic: 90, limit: 90, higher_is_better: false,
        verdict: "pass", note: "The firmware caps it at 90 A", shown: "90.0 A", shown_pessimistic: "90.0 A",
        shown_limit: "at most 90.0 A", shown_margin: "+0%",
      },
    ],
    top_speed_kmh: { full: 110, half: 105, reserve: 100 },
    least_power_speed_ms: 11.6,
    least_power_minutes: 43.3,
    mass_lines: [
      { name: "Frame", grams: mass - 300, group: "base" },
      { name: "Payload in the claws", grams: 100, group: "payload" },
      { name: "Growth margin", grams: 200, group: "margin" },
    ],
    balance: { passed: true, trim_x_mm: -13, center_of_gravity_mm: [0.1, 0, 4.3], busiest_motor_extra: 0.002, inertia_kg_m2: [[0.0129, 0, 0], [0, 0.0154, 0], [0, 0, 0.0258]] },
    numbers: [
      ["Weight, sizing model", `${mass} g`],
      ["Hover time", `${hover} min (22.2 min pessimistic)`],
    ],
  }; // prettier-ignore
}

const SPEC: SpecSheet = {
  schema_version: 1,
  sizing_case: "mission",
  verdict: "pass",
  targets: { reserve_fraction: 0.2, cruise_speed_ms: 10, min_thrust_to_weight: 2 },
  combinations: [combination("base", [], 1860, "39.4"), combination("mission", ["V", "P"], 2408, "25.8")],
  parts: [],
  pack: { cell: "Molicel INR-21700-P45B", cell_id: "molicel-p45b", series: 6, parallel: 2, capacity_mah: 9000, resistance_mohm: 51.1, mass_g: 883 },
};

function answering(body: unknown): typeof fetch {
  return (async () => ({ ok: true, json: async () => body })) as unknown as typeof fetch;
}

test("each combination's numbers show as the report words them, and picking one switches to it", async () => {
  render(<Spec load={{ fromDisk: false, fetcher: answering(SPEC) }} />);
  const base = await screen.findByLabelText("base numbers");
  expect(within(base).getByText("39.4 min (22.2 min pessimistic)")).toBeInTheDocument();
  fireEvent.click(screen.getByRole("tab", { name: "mission" }));
  const mission = screen.getByLabelText("mission numbers");
  expect(within(mission).getByText("2408 g")).toBeInTheDocument();
  expect(screen.getByRole("tab", { name: "mission" })).toHaveAttribute("aria-selected", "true");
  expect(screen.getByRole("heading", { level: 2, name: /mission \(V, P\), required/ })).toBeInTheDocument();
});

test("every check has its target, its margin, and its note", async () => {
  render(<Spec load={{ fromDisk: false, fetcher: answering(SPEC) }} />);
  const checks = await screen.findByRole("region", { name: "base checks" });
  expect(within(checks).getByText("at least 21.0 min")).toBeInTheDocument();
  expect(within(checks).getByText("+23%")).toBeInTheDocument();
  expect(within(checks).getByText(/The firmware caps it at 90 A/)).toBeInTheDocument();
});

test("its weight adds up line by line, the payload and the margin included, and the CAD balances it", async () => {
  render(<Spec load={{ fromDisk: false, fetcher: answering(SPEC) }} />);
  const weight = await screen.findByRole("region", { name: "base weight" });
  expect(within(weight).getByText("Payload in the claws")).toBeInTheDocument();
  expect(within(weight).getByText("1860.0 g")).toBeInTheDocument(); // the whole, as the model has it
  const balance = screen.getByRole("region", { name: "base balance" });
  expect(within(balance).getByText("0.2% harder than the others")).toBeInTheDocument();
  expect(screen.getByRole("region", { name: "the pack" })).toHaveTextContent("6S2P Molicel INR-21700-P45B");
});
