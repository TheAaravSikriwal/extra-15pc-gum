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
      outcome: "62 of 78 runs pass",
      links: [
        { text: "report", url: "#/library/docs/reports/flight-sim/README" },
        { text: "video", url: "https://example.com/v" },
      ],
      side_track: false,
      report: {
        verdict: "fail",
        generated: "2026-10-21",
        url: "#/library/docs/reports/flight-sim/README",
        says: ["Fail. 78 of 78 runs flown, and 16 miss."],
        numbers: [["PX4", "62 of 78 runs pass"]],
        sections: [{ text: "Closing the loop", url: "#/library/docs/reports/flight-sim/README~closing-the-loop" }],
      },
      stills: ["stills/flight-sim/drop-wide.png"],
      logs: [{ title: "The last batch", date: "2026-10-20", url: "#/library/docs/log/2026-10-20-flight-sim-final" }],
      parts: [
        {
          name: "4a. Talk",
          what: "Settle the scenarios",
          status: "Done",
          outcome: "twelve of them",
          links: [{ text: "log", url: "#/library/docs/log/2026-10-19-flight-sim-talk" }],
        },
      ],
      learning: [{ text: "Flight simulation", url: "#/library/docs/learning~8-flight-simulation" }],
    },
    {
      id: "aero",
      number: "",
      name: "Aero (the wind tunnel)",
      purpose: "The virtual wind tunnel",
      status: "In progress",
      outcome: "FluidX3D",
      links: [],
      side_track: true,
      starts_after: "Step 2",
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

test("the steps and the side tracks are tables apart, each linking to its page", async () => {
  render(<Steps load={{ fromDisk: false, fetcher: answering(STEPS) }} />);
  const main = await screen.findByRole("region", { name: "The steps" });
  expect(within(main).getByRole("link", { name: "4. Flight sim (PX4)" })).toHaveAttribute(
    "href",
    stepLink("flight-sim"),
  );
  expect(within(main).getByRole("cell", { name: "fail, 2026-10-21" })).toBeInTheDocument();
  const side = screen.getByRole("region", { name: "Side tracks" });
  expect(within(side).getByRole("link", { name: "Aero (the wind tunnel)" })).toBeInTheDocument();
  expect(within(side).getByRole("cell", { name: "Step 2" })).toBeInTheDocument();
  expect(within(side).getByRole("cell", { name: "The virtual wind tunnel" })).toBeInTheDocument();
});

test("a step's page has its report now, apart from the outcome written when it was done", async () => {
  render(<StepPage id="flight-sim" load={{ fromDisk: false, fetcher: answering(STEPS) }} />);
  const now = await screen.findByRole("region", { name: "the report now" });
  expect(within(now).getByText(/From the report of 2026-10-21, which says fail/)).toBeInTheDocument();
  expect(within(now).getByText("Fail. 78 of 78 runs flown, and 16 miss.")).toBeInTheDocument();
  expect(within(now).getByText("62 of 78 runs pass")).toBeInTheDocument();
  expect(within(now).getByRole("link", { name: "Closing the loop" })).toHaveAttribute(
    "href",
    "#/library/docs/reports/flight-sim/README~closing-the-loop",
  );
  const then = screen.getByRole("region", { name: "the outcome" });
  expect(within(then).getByText(/As I wrote it in the plan/)).toBeInTheDocument();
  // the library's links stay in the tab, the rest open a new one
  expect(within(then).getByRole("link", { name: "report" })).not.toHaveAttribute("target");
  expect(within(then).getByRole("link", { name: "video" })).toHaveAttribute("target", "_blank");
});

test("a step's page has its parts, its pictures, its learning and its log", async () => {
  render(<StepPage id="flight-sim" load={{ fromDisk: false, fetcher: answering(STEPS) }} />);
  expect(await screen.findByRole("cell", { name: "4a. Talk" })).toBeInTheDocument();
  expect(screen.getByRole("cell", { name: "Settle the scenarios" })).toBeInTheDocument();
  expect(screen.getByRole("link", { name: "log" })).toHaveAttribute("href", "#/library/docs/log/2026-10-19-flight-sim-talk");
  expect(screen.getByRole("img", { name: "drop" })).toHaveAttribute("src", "./data/stills/flight-sim/drop-wide.png");
  expect(screen.getByRole("link", { name: "The last batch" })).toBeInTheDocument();
  expect(screen.getByText("2026-10-20")).toBeInTheDocument();
  expect(screen.getByRole("link", { name: "Flight simulation" })).toHaveAttribute(
    "href",
    "#/library/docs/learning~8-flight-simulation",
  );
});

test("a side track says when it starts, and one in progress isn't told as done", async () => {
  render(<StepPage id="aero" load={{ fromDisk: false, fetcher: answering(STEPS) }} />);
  expect(await screen.findByText(/starts after step 2/)).toBeInTheDocument();
  expect(screen.getByRole("heading", { name: "Where it is" })).toBeInTheDocument();
  expect(screen.queryByRole("region", { name: "the report now" })).not.toBeInTheDocument();
});
