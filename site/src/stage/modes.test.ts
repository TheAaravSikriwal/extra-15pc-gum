import { MENU, modeOf, scenarioOf } from "./modes";

test("the route picks the mode: the home is inside the drone, #/fly is flying, the rest are pages", () => {
  expect(modeOf([])).toBe("inside");
  expect(modeOf(["drone"])).toBe("inside"); // the old 3D page's address still lands here
  expect(modeOf(["fly"])).toBe("fly");
  expect(modeOf(["fly", "dead motor"])).toBe("fly");
  expect(modeOf(["spec"])).toBe("page");
  expect(modeOf(["wiring", "fc"])).toBe("page"); // a board's pins, linked from its card
});

test("the scenario comes from the route, hover by default", () => {
  expect(scenarioOf(["fly"])).toBe("hover");
  expect(scenarioOf(["fly", "parachute drop"])).toBe("parachute drop");
});

test("the corner menu has every other page, and not the two the view took over", () => {
  const routes = MENU.map((p) => p.route);
  expect(routes).toEqual(["spec", "flights", "steps", "tunnel", "unproven", "build", "library", "catalog", "data", "math"]);
  expect(routes).not.toContain("drone");
  expect(routes).not.toContain("wiring");
});
