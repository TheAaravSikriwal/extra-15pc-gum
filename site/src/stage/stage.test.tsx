import { fireEvent, render, screen, within } from "@testing-library/react";

import { Menu } from "./Menu";
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
  expect(document.querySelector("svg.blueprint")).not.toBeNull();
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
  expect(screen.getByText("Ten meters up, held for a minute.")).toBeInTheDocument();
});

test("the corner menu opens to every other page", () => {
  render(<Menu />);
  fireEvent.click(screen.getByRole("button", { name: "Menu" }));
  const pages = screen.getByRole("list", { name: "pages" });
  expect(within(pages).getAllByRole("link")).toHaveLength(10);
  expect(within(pages).getByRole("link", { name: "Build it" })).toHaveAttribute("href", "#/build");
});
