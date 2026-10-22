import { fireEvent, render, screen, within } from "@testing-library/react";

import type { Flights as FlightsData, Playback } from "../data/types";
import { FlightView, useRuns } from "./FlightRun";
import { Flights, runLink } from "./Flights";

const INDEX: FlightsData = {
  schema_version: 1,
  scenarios: ["hover", "dead motor", "spiral descent"],
  about: [
    { name: "hover", step: 4, what: "Ten meters up." },
    { name: "dead motor", step: 4, what: "One motor stops." },
    { name: "spiral descent", step: 7, what: "Down on a helix." },
  ],
  setups: ["base", "P"],
  runs: [
    { scenario: "hover", setup: "base", firmware: "px4", flown: true, passed: true, file: "f1" },
    { scenario: "dead motor", setup: "base", firmware: "px4", flown: true, passed: false, file: "f2", missed: "touchdown: 24 m/s" },
    { scenario: "hover", setup: "base", firmware: "mine", flown: true, passed: true, file: "f3" },
    { scenario: "spiral descent", setup: "base", firmware: "mine", flown: true, passed: true, file: "f4" },
  ],
};

function answering(body: unknown): typeof fetch {
  return (async () => ({ ok: true, json: async () => body })) as unknown as typeof fetch;
}

test("both firmwares get a matrix, and a flown cell links to its run", async () => {
  render(<Flights load={{ fromDisk: false, fetcher: answering(INDEX) }} />);
  const px4 = await screen.findByRole("region", { name: "PX4 v1.17.0" });
  expect(within(px4).getByText("PX4 v1.17.0: 1 of 2 pass")).toBeInTheDocument();
  expect(within(px4).getAllByRole("link")[0]).toHaveAttribute("href", runLink("base", "hover"));
  expect(within(px4).queryByText("spiral descent")).toBeNull(); // a row only where it flew
  const mine = screen.getByRole("region", { name: "My firmware" });
  expect(within(mine).getByText("My firmware: 2 of 2 pass")).toBeInTheDocument();
  expect(within(mine).getByText("spiral descent")).toBeInTheDocument();
  expect(runLink("V+C", "dead motor")).toBe("#/flights/V%2BC/dead%20motor");
});

test("each scenario says what it tests and where it flew, by step, and each miss says why", async () => {
  render(<Flights load={{ fromDisk: false, fetcher: answering(INDEX) }} />);
  const tests = await screen.findByRole("region", { name: "what each scenario tests" });
  const flight = within(tests).getByRole("region", { name: "Flight (step 4)" });
  expect(within(flight).getByText("One motor stops.")).toBeInTheDocument();
  expect(within(flight).getByText(/Flown by PX4 in base, and by mine in none yet/)).toBeInTheDocument();
  expect(within(tests).getByRole("region", { name: "Smart features (step 7)" })).toHaveTextContent("Down on a helix.");
  const misses = screen.getByRole("region", { name: "why the misses missed" });
  expect(within(misses).getByText("touchdown: 24 m/s")).toBeInTheDocument();
  // the matrices come per step, in the combinations' one order
  const px4 = screen.getByRole("region", { name: "PX4 v1.17.0" });
  expect(within(px4).getByRole("table", { name: "PX4 v1.17.0, Flight (step 4)" })).toBeInTheDocument();
  expect(within(px4).getByText("Flight (step 4): 1 of 2 pass")).toBeInTheDocument(); // each step's own count
});

function run(firmware: string, passed: boolean): Playback {
  return {
    schema_version: 1,
    scenario: "dead motor",
    setup: "base",
    firmware,
    passed,
    findings: [{ check: "touchdown", passed, detail: passed ? "came down at 0.7 m/s" : "24 m/s" }],
    t: [0, 10, 20, 30],
    position: [
      [0, 0, 0],
      [0, 0, 10],
      [0, 0, 40],
      [0, 0, 0],
    ],
    attitude: [
      [0, 0, 0, 1],
      [0, 0, 0, 1],
      [0, 0, 0, 1],
      [0, 0, 0, 1],
    ],
    motors: [
      [0, 0, 0, 0],
      [560, 560, 560, 560],
      [560, 560, 0, 560],
      [0, 0, 0, 0],
    ],
    events: [
      { at: 2, name: "armed" },
      { at: 22, name: "motor failed" },
    ],
  };
}

test("a run plays both firmwares on one clock, the events appearing as they come", async () => {
  render(<FlightView runs={[run("px4", false), run("mine", false)]} view={(t) => <p>at {t}</p>} />);
  expect(screen.getAllByRole("img", { name: /Height|Speed|Motors/ })).toHaveLength(3);
  const px4 = screen.getByRole("region", { name: "PX4 events" });
  expect(within(px4).queryByText("motor failed")).toBeNull(); // not yet, at 0 s
  fireEvent.click(screen.getByRole("button", { name: /PX4: motor failed/ }));
  expect(await within(px4).findByText(/motor failed/)).toBeInTheDocument(); // next frame
  expect(within(px4).getByText("touchdown: 24 m/s")).toBeInTheDocument();
});

function Runs({ setup, scenario, fetcher }: { setup: string; scenario: string; fetcher: typeof fetch }) {
  const { runs, problem } = useRuns(setup, scenario, LOAD(fetcher));
  return <p>{problem ?? (runs ? `${runs.length} runs` : "loading")}</p>;
}

const loads = new Map<typeof fetch, { fromDisk: boolean; fetcher: typeof fetch }>();
function LOAD(fetcher: typeof fetch) {
  // one options object per fetcher, as a page holds on to its own
  if (!loads.has(fetcher)) loads.set(fetcher, { fromDisk: false, fetcher });
  return loads.get(fetcher)!;
}

test("going from one run's page to another forgets the first one's problem", async () => {
  const fetcher = (async (url: string) => ({
    ok: true,
    json: async () => (url.endsWith("flights.json") ? INDEX : run("px4", true)),
  })) as unknown as typeof fetch;
  const { rerender } = render(<Runs setup="max" scenario="hover" fetcher={fetcher} />);
  expect(await screen.findByText("no flown runs of hover in max")).toBeInTheDocument();
  rerender(<Runs setup="base" scenario="hover" fetcher={fetcher} />);
  expect(await screen.findByText("2 runs")).toBeInTheDocument();
});
