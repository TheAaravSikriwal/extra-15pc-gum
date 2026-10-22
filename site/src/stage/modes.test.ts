import { flyLink, MENU, modeOf, pageName, scenarioOf, setupOf } from "./modes";

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

test("a run's page links into Fly it with its own combination", () => {
  expect(flyLink("dead motor", "V+C")).toBe("#/fly/dead%20motor/V%2BC");
  expect(setupOf(["fly", "dead motor", "V+C"])).toBe("V+C");
  expect(setupOf(["fly", "dead motor"])).toBeNull();
  expect(scenarioOf(["fly", "dead motor", "V+C"])).toBe("dead motor");
});

test("a page's bar names it, deep links included", () => {
  expect(pageName(["spec"])).toBe("Spec sheet");
  expect(pageName(["flights", "max", "dead motor"])).toBe("Every flight");
  expect(pageName(["library", "docs", "STATUS.md"])).toBe("The library");
  expect(pageName(["wiring", "fc"])).toBe("The wiring");
});
