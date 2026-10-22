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

const WIRES3D = {
  schema_version: 1,
  wires: [
    { label: "lead.XT60.+ to esc.BAT.VBAT", harness: "main power", ends: [{ pin: "lead.XT60.+", at_mm: [0, 0, 0], piece: "x" }, { pin: "esc.BAT.VBAT", at_mm: [0, 0, 0], piece: "y" }],
      route: "battery leads", route_piece: "wire battery leads", path_mm: [], awg: 12, diameter_mm: 3.95, wire: "Silicone hookup wire", role: "power", length_mm: 182.7, gaps_mm: [] },
  ],
  connectors: [
    { connector: "lead.XT60", part_id: "base-wiring", estimate: true, url: null, note: "where the leads' route starts" },
    { connector: "esc.BAT", part_id: "holybro-tekko32-f4-50a", estimate: false, url: "https://maker/drawing", note: null },
  ],
}; // prettier-ignore
const WIRES = {
  schema_version: 1,
  routes: [{ name: "battery leads", node: "wire battery leads", wires: [], heating_share: { base: { hover: 0.06, burst: 0.2 }, max: { hover: 0.15, burst: 0.31 } } }],
};

test("every wire with its gauge and cut length, where each plug's pins come from, and how hard each route works", async () => {
  const files: Record<string, unknown> = { "wiring.json": WIRING, "wires3d.json": WIRES3D, "wires.json": WIRES };
  const fetcher = (async (url: string) => ({ ok: true, json: async () => files[String(url).replace("./data/", "")] })) as unknown as typeof fetch;
  render(<Wiring load={{ fromDisk: false, fetcher }} />);
  const harness = await screen.findByRole("table", { name: "the main power harness" });
  expect(within(harness).getByText("183 mm")).toBeInTheDocument();
  expect(within(harness).getByText("12 AWG Silicone hookup wire")).toBeInTheDocument();
  const pins = screen.getByRole("region", { name: "where the pins are" });
  expect(within(pins).getByText(/My estimate: where the leads/)).toBeInTheDocument();
  expect(within(pins).getByRole("link", { name: "The maker's drawing" })).toHaveAttribute("href", "https://maker/drawing");
  const heat = screen.getByRole("region", { name: "how hard the wires work" });
  expect(within(heat).getByText("31%")).toBeInTheDocument(); // max's worst, the burst
});
