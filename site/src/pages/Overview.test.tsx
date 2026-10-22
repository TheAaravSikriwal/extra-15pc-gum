import { render, screen, within } from "@testing-library/react";

import { Overview } from "./Overview";

const SPEC = {
  schema_version: 1,
  sizing_case: "mission",
  verdict: "fail",
  targets: {},
  parts: [],
  combinations: [
    { name: "mission", modules: ["V", "P"], verdict: "pass", required: true, mass_g: 2408.3, growth_margin_g: 200, checks: [
      { name: "Hover time", unit: "min", nominal: 25.89, pessimistic: 22.27, higher_is_better: true, verdict: "pass", note: "", shown: "25.8 min", shown_pessimistic: "22.2 min" },
    ], top_speed_kmh: {}, least_power_speed_ms: 12, least_power_minutes: 33, mass_lines: [], numbers: [] },
    { name: "max", modules: ["V", "P", "C"], verdict: "fail", required: false, mass_g: 2620.4, growth_margin_g: 200, checks: [],
      top_speed_kmh: {}, least_power_speed_ms: 12, least_power_minutes: 30, mass_lines: [], numbers: [] },
  ],
}; // prettier-ignore
const STEPS = {
  schema_version: 1,
  steps: [{ id: "sizing", number: "1", name: "Sizing and parts", purpose: "", status: "Done, 2026-10-17", outcome: "", links: [], side_track: false, stills: [], logs: [], parts: [], learning: [] }],
}; // prettier-ignore

function serving(files: Record<string, unknown>): typeof fetch {
  return (async (url: string) => {
    const name = String(url).replace("./data/", "");
    return { ok: name in files, json: async () => files[name] };
  }) as unknown as typeof fetch;
}

test("the overview: the modules, every combination with its weight, hover and verdict, and each step", async () => {
  render(<Overview load={{ fromDisk: false, fetcher: serving({ "spec.json": SPEC, "steps.json": STEPS }) }} />);
  const combinations = await screen.findByRole("region", { name: "the combinations" });
  expect(within(combinations).getByText("2408 g")).toBeInTheDocument();
  expect(within(combinations).getByText("25.8 min / 22.2 min")).toBeInTheDocument();
  expect(within(combinations).getByText("fail")).toBeInTheDocument();
  expect(within(combinations).getByText(", optional")).toBeInTheDocument(); // max isn't required
  expect(screen.getByRole("region", { name: "the modules" })).toHaveTextContent("P: the parachute");
  expect(screen.getByRole("link", { name: "1. Sizing and parts" })).toHaveAttribute("href", "#/steps/sizing");
  // and a line on every page of the docs
  const docs = screen.getByRole("region", { name: "these docs" });
  expect(within(docs).getByRole("link", { name: "Wind tunnel" })).toHaveAttribute("href", "#/tunnel");
  expect(within(docs).getAllByRole("link").length).toBeGreaterThanOrEqual(11);
});
