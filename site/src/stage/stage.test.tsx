import { cleanup, fireEvent, render, screen, within } from "@testing-library/react";

import { Contents, Menu } from "./Menu";
import { Stage } from "./Stage";

function serving(files: Record<string, unknown>): typeof fetch {
  return (async (url: string) => {
    const name = String(url).replace("./data/", "");
    if (!(name in files)) return { ok: false, json: async () => ({}), arrayBuffer: async () => new ArrayBuffer(0) };
    return { ok: true, json: async () => files[name] };
  }) as unknown as typeof fetch;
}

const FLIGHTS = {
  schema_version: 1,
  scenarios: ["hover", "parachute drop", "spiral descent"],
  about: [
    { name: "hover", step: 4, what: "Ten meters up, held for a minute." },
    { name: "parachute drop", step: 4, what: "Forty meters up, the chute fires." },
    { name: "spiral descent", step: 7, what: "Down from 40 m on a helix." },
  ],
  setups: ["max"],
  runs: [
    { scenario: "hover", setup: "max", firmware: "mine", flown: true, passed: true, file: "flights/max-hover-mine.json" },
    { scenario: "parachute drop", setup: "max", firmware: "px4", flown: true, passed: true, file: "x" },
    { scenario: "spiral descent", setup: "max", firmware: "mine", flown: true, passed: true, file: "y" },
  ],
};
const load = { fromDisk: false, fetcher: serving({ "flights.json": FLIGHTS }) };
const scene = () => <div data-testid="scene" />;

test("inside the drone: the blueprint behind it, the switch at the top, the controls beside it", () => {
  render(<Stage route={[]} load={load} scene={scene} />);
  expect(screen.getByTestId("stage")).toHaveClass("inside");
  expect(document.querySelectorAll(".blueprint svg.bp-figure")).toHaveLength(4); // each drawing on its own
  expect(screen.getByRole("link", { name: "Inside it" })).toHaveAttribute("aria-current", "page");
  expect(screen.getByRole("complementary", { name: "inside it" })).toBeInTheDocument();
});

test("flying keeps the same drone: only the mode and the interface around it change", async () => {
  const { rerender } = render(<Stage route={[]} load={load} scene={scene} />);
  const drone = screen.getByTestId("scene");
  rerender(<Stage route={["fly"]} load={load} scene={scene} />);
  expect(screen.getByTestId("scene")).toBe(drone); // never unmounted
  expect(screen.getByTestId("stage")).toHaveClass("fly");
  const list = await screen.findByRole("group", { name: "scenarios" });
  // max on my firmware: hover flown, the drop only on PX4, so it says so instead of linking
  const flight = within(list).getByRole("region", { name: "Flight" });
  expect(within(flight).getByRole("link", { name: "hover" })).toHaveAttribute("href", "#/fly/hover");
  expect(within(flight).queryByRole("link", { name: "parachute drop" })).toBeNull();
  expect(within(flight).getByText("Not flown in max: parachute drop")).toBeInTheDocument();
  rerender(<Stage route={["fly", "parachute drop"]} load={load} scene={scene} />);
  expect(screen.getByText(/It wasn.t flown in max/)).toBeInTheDocument();
  rerender(<Stage route={["fly"]} load={load} scene={scene} />);
  // the later steps' runs in their own group, and what the playing one tests
  const smart = within(list).getByRole("region", { name: "Smart features" });
  expect(within(smart).getByRole("link", { name: "spiral descent" })).toBeInTheDocument();
  expect(document.querySelector(".stage-panel .about")).toHaveTextContent("Ten meters up, held for a minute.");
});

test("the corner menu opens to every other page", () => {
  render(<Menu />);
  fireEvent.click(screen.getByRole("button", { name: "Menu" }));
  const pages = screen.getByRole("list", { name: "pages" });
  expect(within(pages).getAllByRole("link")).toHaveLength(12);
  expect(within(pages).getByRole("list", { name: "Tested" })).toBeInTheDocument();
  expect(within(pages).getByRole("link", { name: "Build it" })).toHaveAttribute("href", "#/build");
});

test("on a page, the contents are always there, with the page you're on marked", () => {
  render(<Contents current="steps" />);
  const contents = screen.getByRole("navigation", { name: "contents" });
  expect(within(contents).getAllByRole("link")).toHaveLength(12);
  expect(within(contents).getByRole("link", { name: "Steps" })).toHaveAttribute("aria-current", "page");
  expect(within(contents).getByRole("link", { name: "Parts" })).not.toHaveAttribute("aria-current");
  expect(screen.queryByRole("button", { name: "Menu" })).toBeNull(); // nothing to click open
});

const WIRES3D = {
  schema_version: 1,
  wires: [
    {
      label: "rx.pads.TX to fc.RC.USART6_RX",
      harness: "receiver",
      ends: [
        { pin: "rx.pads.TX", at_mm: [-56, 0, 20], piece: "radiomaster-rp2-v2" },
        { pin: "fc.RC.USART6_RX", at_mm: [16, 6, 22], piece: "ark-fpv" },
      ],
      route: null,
      route_piece: null,
      path_mm: [],
      awg: 26,
      diameter_mm: 1.1,
      wire: "Thin silicone signal lead",
      role: "signal",
      length_mm: 90,
      gaps_mm: [],
    },
  ],
  connectors: [],
};

test("a harness isolates its wires, and a wire picked from it opens its card", async () => {
  const files = { "flights.json": FLIGHTS, "wires3d.json": WIRES3D };
  render(<Stage route={[]} load={{ fromDisk: false, fetcher: serving(files) }} scene={scene} />);
  const harness = await screen.findByRole("combobox", { name: "harness" });
  fireEvent.change(harness, { target: { value: "receiver" } });
  fireEvent.change(screen.getByRole("combobox", { name: "wire" }), { target: { value: "rx.pads.TX to fc.RC.USART6_RX" } });
  expect(screen.getByRole("region", { name: "picked wire" })).toBeInTheDocument();
  fireEvent.click(screen.getByRole("button", { name: "Back to the whole drone" }));
  expect(screen.queryByRole("region", { name: "picked wire" })).toBeNull();
});

test("a scenario only PX4 flew offers PX4, and switching to it plays that run", async () => {
  render(<Stage route={["fly", "parachute drop"]} load={load} scene={scene} />);
  const list = await screen.findByRole("group", { name: "scenarios" });
  expect(within(list).queryByRole("link", { name: "parachute drop" })).toBeNull(); // not on mine
  fireEvent.click(screen.getByRole("button", { name: "PX4" }));
  expect(screen.getByText("max, PX4")).toBeInTheDocument();
  expect(within(screen.getByRole("group", { name: "scenarios" })).getByRole("link", { name: "parachute drop" })).toBeInTheDocument();
});

// a made-up hover at 20 Hz: up to 10 m, held, and down
function hover() {
  const t: number[] = [];
  const position: number[][] = [];
  for (let k = 0; k <= 60 * 20; k++) {
    const s = k / 20;
    t.push(s);
    position.push([0, 0, s < 2 ? 0 : s < 7 ? (s - 2) * 2 : s < 50 ? 10 : Math.max(0, 10 - (s - 50) * 2)]);
  }
  return {
    schema_version: 1, scenario: "hover", setup: "max", firmware: "mine", passed: true, findings: [], t, position,
    attitude: t.map(() => [0, 0, 0, 1]), motors: t.map(() => [560, 560, 560, 560]),
    events: [{ at: 2.1, name: "took off" }, { at: 7, name: "hold" }, { at: 55, name: "landed" }],
  }; // fmt: skip
}

test("each scenario says what it tests in a line, and the run plays out in a strip under the drone", async () => {
  const flights = { ...FLIGHTS, runs: FLIGHTS.runs.map((r) => (r.scenario === "hover" ? { ...r, glyph: { kind: "profile", points: [[0, 0], [0.5, 1], [1, 0]] } } : r)) };
  const files = { "flights.json": flights, "flights/max-hover-mine.json": hover() };
  render(<Stage route={["fly", "hover"]} load={{ fromDisk: false, fetcher: serving(files) }} scene={scene} />);
  const link = await screen.findByRole("link", { name: "hover" });
  expect(link).toHaveAccessibleDescription("Ten meters up, held for a minute.");
  expect(link.querySelector("svg.glyph polyline")).not.toBeNull(); // its run, drawn
  const strip = await screen.findByRole("region", { name: "the run" });
  expect(within(strip).getByRole("img", { name: /from above/ })).toBeInTheDocument();
  expect(within(strip).getByRole("slider", { name: "the run's time" })).toHaveAttribute("aria-valuemax", "55");
  expect(within(strip).getByText("Taking off")).toBeInTheDocument();
  expect(within(strip).getByText("Height · top 10 m")).toBeInTheDocument();
  // the strip is only for flying
  cleanup();
  render(<Stage route={[]} load={load} scene={scene} />);
  expect(screen.queryByRole("region", { name: "the run" })).toBeNull();
});

test("a link that names a combination flies the run in it", async () => {
  render(<Stage route={["fly", "hover", "base"]} load={load} scene={scene} />);
  expect(await screen.findByText(/^base, my firmware$/)).toBeInTheDocument();
});

test("on a phone the controls sit in a drawer that opens and closes", () => {
  render(<Stage route={[]} load={load} scene={scene} />);
  const handle = screen.getByRole("button", { name: "Show the controls" });
  expect(handle).toHaveAttribute("aria-expanded", "false");
  fireEvent.click(handle);
  expect(screen.getByRole("button", { name: "Hide the controls" })).toHaveAttribute("aria-expanded", "true");
  expect(document.querySelector(".stage-drawer")).toHaveClass("open");
  // the drawer stays open from one mode into the other
  fireEvent.click(screen.getByRole("button", { name: "Hide the controls" }));
  expect(document.querySelector(".stage-drawer")).not.toHaveClass("open");
});

test("on a phone, picking a run closes the drawer, so the drone's there to watch", () => {
  const { rerender } = render(<Stage route={["fly", "hover"]} load={load} scene={scene} />);
  fireEvent.click(screen.getByRole("button", { name: "Show the controls" }));
  expect(document.querySelector(".stage-drawer")).toHaveClass("open");
  rerender(<Stage route={["fly", "spiral descent"]} load={load} scene={scene} />);
  expect(document.querySelector(".stage-drawer")).not.toHaveClass("open");
});

const TUNNEL = {
  schema_version: 1,
  fork_public: false,
  note: "pictures",
  stills: [],
  cases: [],
  flows: [
    { name: "Max-cruise", direction: "front", label: "From the front", about: "10 m/s nose first.", file: "tunnel/flow/Max-cruise.json" },
    { name: "Max-above", direction: "above", label: "From above", about: "10 m/s down onto its top.", file: "tunnel/flow/Max-above.json" },
    { name: "left", direction: "left", label: "From the left", about: "10 m/s on its left side.", file: null },
  ],
};
const CRUISE_FLOW = {
  schema_version: 1,
  name: "Max-cruise",
  direction: "front",
  setup: "Max",
  speed: 10,
  color_max: 17,
  force_n: 1.84,
  pitch_deg: 3.3,
  loop_s: 0.25,
  frames: 64,
  particles: { file: "tunnel/flow/Max-cruise-particles.bin", count: 2400 },
  slice: { file: "tunnel/flow/Max-cruise-slice.bin", width: 256, height: 144, corners: [[0, 0, 0], [1, 0, 0], [1, 0, -1], [0, 0, -1]] },
};

test("the wind tunnel in Fly it: each way the air comes, and the one picked with its colors and force", async () => {
  const files = { "flights.json": FLIGHTS, "tunnel.json": TUNNEL, "tunnel/flow/Max-cruise.json": CRUISE_FLOW };
  const fetcher = serving(files);
  const { rerender } = render(<Stage route={["fly", "hover"]} load={{ fromDisk: false, fetcher }} scene={scene} />);
  const tunnel = await screen.findByRole("region", { name: "Wind tunnel" });
  const front = within(tunnel).getByRole("link", { name: "From the front" });
  expect(front).toHaveAttribute("href", "#/fly/tunnel/front");
  expect(front).toHaveAccessibleDescription("10 m/s nose first.");
  expect(within(tunnel).getByRole("link", { name: "From above" })).toBeInTheDocument();
  // one not run yet is listed, but not as a link
  expect(within(tunnel).queryByRole("link", { name: "From the left" })).toBeNull();
  expect(within(tunnel).getByLabelText("From the left, not run yet")).toBeInTheDocument();
  rerender(<Stage route={["fly", "tunnel", "front"]} load={{ fromDisk: false, fetcher }} scene={scene} />);
  const now = await screen.findByRole("region", { name: "the wind tunnel" });
  expect(await within(now).findByText(/FluidX3D says 1\.8 N along the wind/)).toBeInTheDocument();
  expect(within(now).getByRole("checkbox", { name: "speed slice" })).toBeChecked();
  expect(screen.getByText(/max, wind tunnel/i)).toBeInTheDocument(); // the tunnel ran around Max
  expect(screen.getByRole("link", { name: "From the front" })).toHaveAttribute("aria-current", "true");
  expect(screen.getByRole("link", { name: "hover" })).not.toHaveAttribute("aria-current"); // no run plays
  const strip = screen.getByRole("region", { name: "the air" });
  expect(within(strip).getByText("From the front")).toBeInTheDocument();
  expect(within(strip).getByText("10 m/s")).toBeInTheDocument();
});

test("flying, a quiet line under the intro says how to look around, with a mouse for each", async () => {
  const { rerender } = render(<Stage route={[]} load={load} scene={scene} />);
  expect(screen.queryByRole("list", { name: "looking around" })).toBeNull(); // only in Fly it
  rerender(<Stage route={["fly", "hover"]} load={load} scene={scene} />);
  const hint = screen.getByRole("list", { name: "looking around" });
  expect(within(hint).getAllByText("Drag")).toHaveLength(2); // the mouse's and the finger's
  expect(within(hint).getByText("Scroll")).toBeInTheDocument();
  expect(within(hint).getByText("Right-drag")).toBeInTheDocument();
  expect(within(hint).getByText("Pinch")).toBeInTheDocument();
});
