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
  scenarios: ["hover", "parachute drop"],
  setups: ["max"],
  runs: [
    { scenario: "hover", setup: "max", firmware: "mine", flown: true, passed: true, file: "flights/max-hover-mine.json" },
    { scenario: "parachute drop", setup: "max", firmware: "px4", flown: true, passed: true, file: "x" },
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
  const list = await screen.findByRole("list", { name: "scenarios" });
  // max on my firmware: hover flown, the drop only on PX4, so it says so by not linking
  expect(within(list).getByRole("link", { name: "hover" })).toHaveAttribute("href", "#/fly/hover");
  expect(within(list).queryByRole("link", { name: "parachute drop" })).toBeNull();
});

test("the corner menu opens to every other page", () => {
  render(<Menu />);
  fireEvent.click(screen.getByRole("button", { name: "Menu" }));
  const pages = screen.getByRole("list", { name: "pages" });
  expect(within(pages).getAllByRole("link")).toHaveLength(10);
  expect(within(pages).getByRole("link", { name: "Build it" })).toHaveAttribute("href", "#/build");
});
