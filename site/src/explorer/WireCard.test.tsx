import { fireEvent, render, screen } from "@testing-library/react";

import type { PinSource, Wire3d } from "../data/types";
import { WireCard } from "./WireCard";

const WIRE: Wire3d = {
  label: "fc.ESC.CH1 to cut.J1.NC1",
  harness: "esc cable",
  ends: [
    { pin: "fc.ESC.CH1", at_mm: [16.3, -5.15, 22], piece: "ark-fpv" },
    { pin: "cut.J1.NC1", at_mm: [61, -7.6, 26], piece: "cjmcu-5018" },
  ],
  route: "esc cable to switch",
  route_piece: "wire esc cable to switch",
  path_mm: [[20, 0, 22]],
  awg: 28,
  diameter_mm: 0.9,
  wire: "Thin silicone signal lead",
  role: "signal",
  length_mm: 52.4,
  gaps_mm: [],
};

const SOURCES: PinSource[] = [
  { connector: "fc.ESC", part_id: "ark-fpv", estimate: false, url: "https://docs.arkelectron.com/x", note: "scaled" },
  { connector: "cut.J1", part_id: "cjmcu-5018", estimate: true, url: null, note: "only a seller's photo" },
];

test("a picked wire's card: both ends, its gauge and type, and where to cut it", () => {
  render(<WireCard wire={WIRE} sources={SOURCES} onClose={() => {}} />);
  expect(screen.getByRole("heading", { name: "fc.ESC.CH1 to cut.J1.NC1" })).toBeInTheDocument();
  expect(screen.getByText("28 AWG Thin silicone signal lead")).toBeInTheDocument();
  expect(screen.getByText("52 mm")).toBeInTheDocument();
  expect(screen.getByText("esc cable")).toBeInTheDocument();
});

test("it says where each end's pins came from: a maker's drawing, or my estimate", () => {
  render(<WireCard wire={WIRE} sources={SOURCES} onClose={() => {}} />);
  expect(screen.getByRole("link", { name: "the maker's drawing" })).toHaveAttribute("href", "https://docs.arkelectron.com/x");
  expect(screen.getByText(/my estimate: only a seller's photo/)).toBeInTheDocument();
});

test("it can go back to the whole drone", () => {
  let closed = false;
  render(<WireCard wire={WIRE} sources={SOURCES} onClose={() => (closed = true)} />);
  fireEvent.click(screen.getByRole("button", { name: "Back to the whole drone" }));
  expect(closed).toBe(true);
});
