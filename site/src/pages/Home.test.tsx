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

function answering(body: unknown): typeof fetch {
  return (async () => ({ ok: true, json: async () => body })) as unknown as typeof fetch;
}

test("it lists every step's report, found or not yet", async () => {
  render(<Home load={{ fromDisk: false, fetcher: answering(INDEX) }} />);
  expect(await screen.findByText(/Sizing and parts: pass/)).toBeInTheDocument();
  expect(screen.getByText(/Flight sim: not there yet/)).toBeInTheDocument();
  expect(screen.getByText(/Made 2026-10-20 from abc1234/)).toBeInTheDocument();
});

test("stale data says how to fix it", async () => {
  render(<Home load={{ fromDisk: false, fetcher: answering({ ...INDEX, schema_version: 7 }) }} />);
  expect(await screen.findByRole("alert")).toHaveTextContent(/rerun pcs14 site/);
});
