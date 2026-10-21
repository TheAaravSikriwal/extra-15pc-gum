import { act, fireEvent, render, screen } from "@testing-library/react";

import type { Tunnel as TunnelData, TunnelCase } from "../data/types";
import { CaseView, frameAt, Tunnel } from "./Tunnel";

const RUN: TunnelCase = {
  name: "Max-cruise",
  label: "Cruise",
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

test("the page has the cases, the stills and what they can't be trusted for", async () => {
  render(<Tunnel load={{ fromDisk: false, fetcher: answering(TUNNEL) }} />);
  expect(await screen.findByRole("region", { name: "Cruise" })).toBeInTheDocument();
  expect(screen.getByText("Pictures, not measurements.")).toBeInTheDocument();
  expect(screen.getByText(/local preview/)).toBeInTheDocument();
  expect(screen.getByRole("img", { name: "The drag lines: 10 m/s" })).toHaveAttribute(
    "src",
    "./data/tunnel/Max-cruise-side-streamlines.jpg",
  );
});
