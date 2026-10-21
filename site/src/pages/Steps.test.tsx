import { render, screen, within } from "@testing-library/react";

import type { Steps as StepsData } from "../data/types";
import { StepPage, Steps, stepLink } from "./Steps";

const STEPS: StepsData = {
  schema_version: 1,
  steps: [
    {
      id: "flight-sim",
      number: "4",
      name: "Flight sim (PX4)",
      purpose: "Prove the airframe flies",
      status: "Done, 2026-10-20",
      outcome: "62 of 78 runs pass (report, log)",
      links: [{ text: "report", url: "https://github.com/x/docs/reports/flight-sim/README.md" }],
      side_track: false,
      report: { verdict: "fail", generated: "2026-10-20", url: "https://github.com/x/r" },
      stills: ["stills/flight-sim/matrix.png"],
      logs: [{ title: "2026-10-20: The last batch", date: "2026-10-20", url: "https://github.com/x/l" }],
      parts: [{ name: "4a. Talk", what: "the scenarios", status: "Done", outcome: "twelve of them" }],
      learning: [{ text: "Flight simulation", url: "https://github.com/x/docs/learning.md#8-flight-simulation" }],
    },
    {
      id: "aero",
      number: "",
      name: "Aero (the wind tunnel)",
      purpose: "Drag and pictures",
      status: "In progress",
      outcome: "",
      links: [],
      side_track: true,
      report: null,
      stills: [],
      logs: [],
      parts: [],
      learning: [],
    },
  ],
};

function answering(body: unknown): typeof fetch {
  return (async () => ({ ok: true, json: async () => body })) as unknown as typeof fetch;
}

test("the steps and the side tracks are listed apart, each linking to its page", async () => {
  render(<Steps load={{ fromDisk: false, fetcher: answering(STEPS) }} />);
  const main = await screen.findByRole("region", { name: "The steps" });
  expect(within(main).getByRole("link", { name: "4. Flight sim (PX4)" })).toHaveAttribute(
    "href",
    stepLink("flight-sim"),
  );
  const side = screen.getByRole("region", { name: "Side tracks" });
  expect(within(side).getByRole("link", { name: "Aero (the wind tunnel)" })).toBeInTheDocument();
});

test("a step's page has its outcome, its parts, its pictures and its log", async () => {
  render(<StepPage id="flight-sim" load={{ fromDisk: false, fetcher: answering(STEPS) }} />);
  expect(await screen.findByText("62 of 78 runs pass (report, log)")).toBeInTheDocument();
  expect(screen.getByText(/the report says fail/)).toBeInTheDocument();
  expect(screen.getByRole("cell", { name: "4a. Talk" })).toBeInTheDocument();
  expect(screen.getByRole("img", { name: "matrix" })).toHaveAttribute("src", "./data/stills/flight-sim/matrix.png");
  expect(screen.getByRole("link", { name: "2026-10-20: The last batch" })).toBeInTheDocument();
  expect(screen.getByRole("link", { name: "Flight simulation" })).toHaveAttribute(
    "href",
    "https://github.com/x/docs/learning.md#8-flight-simulation",
  );
});
