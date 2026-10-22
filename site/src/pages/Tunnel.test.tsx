import { act, fireEvent, render, screen, within } from "@testing-library/react";

import type { Tunnel as TunnelData, TunnelCase } from "../data/types";
import { CaseView, frameAt, Tunnel } from "./Tunnel";

const RUN: TunnelCase = {
  name: "Max-cruise",
  label: "From the front",
  direction: "front",
  about: "Flying nose first at 10 m/s.",
  grid: "352 x 804 x 276",
  cell_mm: 3.98,
  steps: 21440,
  air_s: 0.64,
  box_m: [1.4, 3.2, 1.1],
  force_n: 1.97,
  frames: [10, 20, 30].map((ms, k) => ({
    step: (k + 1) * 100,
    t_s: ms / 1000,
    files: {
      "side-speed": `tunnel/Max-cruise/side-speed-${k}.jpg`,
      "quarter-vortices": `tunnel/Max-cruise/quarter-vortices-${k}.jpg`,
    },
  })),
};

const TUNNEL: TunnelData = {
  schema_version: 1,
  fork_public: false,
  note: "Pictures, not measurements.",
  stills: [
    {
      case: "Max-cruise",
      view: "side-streamlines",
      title: "The drag lines",
      subtitle: "10 m/s",
      number: "10 m/s",
      caption: "A picture, not a measurement",
      file: "tunnel/Max-cruise-side-streamlines.jpg",
    },
  ],
  cases: [RUN],
};

function answering(body: unknown): typeof fetch {
  return (async () => ({ ok: true, json: async () => body })) as unknown as typeof fetch;
}

test("the frame for a moment is the last one at or before it", () => {
  expect(frameAt(RUN.frames, 0)).toBe(0);
  expect(frameAt(RUN.frames, 0.025)).toBe(1);
  expect(frameAt(RUN.frames, 1)).toBe(2);
});

test("the frames play in order at their time step, in slow motion", async () => {
  let now = 0;
  render(<CaseView run={RUN} now={() => now} />);
  const shown = () => screen.getByRole("img").getAttribute("src");
  expect(shown()).toBe("./data/tunnel/Max-cruise/side-speed-0.jpg");
  fireEvent.click(screen.getByRole("button", { name: "Play" }));
  // at 0.02x, 1.25 s on the page is 25 ms of air: the second frame
  await act(async () => {
    now += 1250;
    await new Promise((r) => requestAnimationFrame(r));
  });
  expect(shown()).toBe("./data/tunnel/Max-cruise/side-speed-1.jpg");
  await act(async () => {
    now += 1000;
    await new Promise((r) => requestAnimationFrame(r));
  });
  expect(shown()).toBe("./data/tunnel/Max-cruise/side-speed-2.jpg");
  // another view plays on the same clock
  fireEvent.click(screen.getByRole("button", { name: /vortices/ }));
  expect(shown()).toBe("./data/tunnel/Max-cruise/quarter-vortices-2.jpg");
});

test("the page has every case in one table with how it was run and its force, and each case its stills", async () => {
  render(<Tunnel load={{ fromDisk: false, fetcher: answering(TUNNEL) }} />);
  const table = await screen.findByRole("region", { name: "the cases" });
  expect(within(table).getByText("352 x 804 x 276, 3.98 mm")).toBeInTheDocument();
  expect(within(table).getByText("2.0 N")).toBeInTheDocument();
  expect(within(table).getByText("1.4 x 3.2 x 1.1 m")).toBeInTheDocument();
  expect(screen.getByText(/Pictures, not measurements\./)).toBeInTheDocument(); // said once, up top
  expect(screen.getByText(/local preview/)).toBeInTheDocument();
  expect(screen.getByRole("region", { name: "how it was run" })).toHaveTextContent("actuator disk");
  // the still sits with its own case
  const front = screen.getByRole("region", { name: "From the front" });
  expect(within(front).getByRole("img", { name: "The drag lines: 10 m/s" })).toHaveAttribute(
    "src",
    "./data/tunnel/Max-cruise-side-streamlines.jpg",
  );
});
