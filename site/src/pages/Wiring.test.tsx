import { render, screen, within } from "@testing-library/react";

import type { Wiring as WiringData } from "../data/types";
import { boardsOf, Wiring, wiringLink } from "./Wiring";

const WIRING: WiringData = {
  schema_version: 1,
  boards: [
    {
      name: "fc",
      part: "ark-fpv",
      module: "base",
      pins: [{ pin: "ESC.CH1", role: "both", functions: "FMU_CH1", to: "cut.J1.NC1", harness: "esc cable" }],
    },
    {
      name: "teensy",
      part: "pjrc-teensy-41",
      module: "base",
      pins: [{ pin: "pins.22", role: "both", functions: "", to: "taps.B2.Y", harness: "safety monitor" }],
    },
  ],
  harnesses: [{ name: "main power", file: "wiring/main-power.svg" }],
  schematic: "wiring/schematic.svg",
  kicad: "https://github.com/x/electrical.kicad_sch",
};

function answering(body: unknown): typeof fetch {
  return (async () => ({ ok: true, json: async () => body })) as unknown as typeof fetch;
}

test("a board's pin map says where every used pin goes", async () => {
  render(<Wiring board="teensy" load={{ fromDisk: false, fetcher: answering(WIRING) }} />);
  const pins = await screen.findByRole("region", { name: "teensy's pins" });
  expect(within(pins).getByRole("cell", { name: "taps.B2.Y" })).toBeInTheDocument();
  expect(screen.getByRole("img", { name: "the main power harness" })).toHaveAttribute(
    "src",
    "./data/wiring/main-power.svg",
  );
  expect(screen.getByRole("link", { name: "its KiCad file" })).toBeInTheDocument();
});

test("without a board named it opens on the flight controller", async () => {
  render(<Wiring load={{ fromDisk: false, fetcher: answering(WIRING) }} />);
  expect(await screen.findByRole("region", { name: "fc's pins" })).toBeInTheDocument();
  expect(wiringLink("fc")).toBe("#/wiring/fc");
});

test("a 3D piece knows which boards it is, by its part", () => {
  expect(boardsOf(WIRING, "ark-fpv")).toEqual(["fc"]);
  expect(boardsOf(WIRING, "gemfan-1050x3")).toEqual([]);
  expect(boardsOf(null, "ark-fpv")).toEqual([]);
});
