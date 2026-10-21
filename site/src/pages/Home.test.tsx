import { render, screen } from "@testing-library/react";

import { Home } from "./Home";

const INDEX = {
  schema_version: 1,
  generated: "2026-10-20",
  commit: "abc1234",
  reports: {
    sizing: { file: "sizing/sizing.json", found: true, verdict: "pass" },
    "flight-sim": { file: "flight-sim/flight-sim.json", found: false },
  },
  files: ["spec.json"],
};

const UNPROVEN = {
  schema_version: 1,
  groups: [{ name: "The whole drone", url: "u", items: [{ what: "Real thrust", measure: "A thrust stand" }] }],
};

const STEPS = {
  schema_version: 1,
  steps: [
    { id: "sizing", number: "1", name: "Sizing and parts", status: "Done, 2026-10-18", side_track: false },
    { id: "firmware", number: "5", name: "My own firmware", status: "In progress", side_track: false },
    { id: "aero", number: "", name: "Aero (the wind tunnel)", status: "In progress", side_track: true },
  ].map((s) => ({ purpose: "", outcome: "", links: [], report: null, stills: [], logs: [], parts: [], ...s })),
};

// answers each data file by its name; anything else isn't there
function answering(files: Record<string, unknown>): typeof fetch {
  return (async (url: string) => {
    const name = url.split("/").pop() ?? "";
    return name in files
      ? { ok: true, json: async () => files[name] }
      : { ok: false, json: async () => ({}) };
  }) as unknown as typeof fetch;
}

test("the home page is the drone and one quiet line per step", async () => {
  const files = { "index.json": INDEX, "steps.json": STEPS, "unproven.json": UNPROVEN };
  render(<Home load={{ fromDisk: false, fetcher: answering(files) }} />);
  const steps = await screen.findByRole("list", { name: "steps" });
  expect(steps.querySelectorAll("li")).toHaveLength(2); // the side track goes on its own line
  expect(screen.getByRole("link", { name: "5. My own firmware" })).toHaveAttribute("href", "#/steps/firmware");
  expect(screen.getByText(/Side tracks/)).toHaveTextContent("Aero (the wind tunnel)");
  expect(screen.getByRole("img", { name: /The drone in CAD/ }).closest("a")).toHaveAttribute("href", "#/drone");
  expect(screen.getByText(/Made 2026-10-20 from abc1234/)).toBeInTheDocument();
  // what the sims can't prove, one click away
  expect(await screen.findByRole("link", { name: "What the sims can't prove" })).toHaveAttribute("href", "#/unproven");
  expect(screen.getByText(/1 thing, and what to measure first/)).toBeInTheDocument();
});

test("without the steps' file it lists every step's report, found or not yet", async () => {
  render(<Home load={{ fromDisk: false, fetcher: answering({ "index.json": INDEX }) }} />);
  expect(await screen.findByText(/Sizing and parts: pass/)).toBeInTheDocument();
  expect(screen.getByText(/Flight sim: not there yet/)).toBeInTheDocument();
});

test("stale data says how to fix it", async () => {
  render(<Home load={{ fromDisk: false, fetcher: answering({ "index.json": { ...INDEX, schema_version: 7 } }) }} />);
  expect(await screen.findByRole("alert")).toHaveTextContent(/rerun pcs14 site/);
});
