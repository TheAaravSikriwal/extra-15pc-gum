import { flyLink, MENU, MENU_GROUPS, modeOf, pageName, pageOf, scenarioOf, setupOf, tunnelLink, tunnelOf } from "./modes";

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

test("the corner menu is the docs, grouped like a manual, and each page has its name on top", () => {
  expect(MENU_GROUPS.map((g) => g.name)).toEqual(["The drone", "Tested", "The work", "Reference"]);
  const routes = MENU.map((p) => p.route);
  expect(routes).toEqual(["overview", "spec", "parts", "wiring", "flights", "tunnel", "unproven", "steps", "build", "library", "data", "math"]);
  expect(routes).not.toContain("drone"); // the drone in 3D is the view itself
  expect(pageName(["wiring", "fc"])).toBe("Wiring");
  expect(pageName(["catalog"])).toBe("Parts"); // its old address
  expect(pageOf(["catalog"])).toBe("parts");
  expect(pageOf(["steps", "sizing"])).toBe("steps"); // a step's page is under Steps
});

test("a run's page links into Fly it with its own combination", () => {
  expect(flyLink("dead motor", "V+C")).toBe("#/fly/dead%20motor/V%2BC");
  expect(setupOf(["fly", "dead motor", "V+C"])).toBe("V+C");
  expect(setupOf(["fly", "dead motor"])).toBeNull();
  expect(scenarioOf(["fly", "dead motor", "V+C"])).toBe("dead motor");
});

test("a page's bar names it, deep links included", () => {
  expect(pageName(["spec"])).toBe("Spec sheet");
  expect(pageName(["flights", "max", "dead motor"])).toBe("Flights");
  expect(pageName(["library", "docs", "STATUS.md"])).toBe("Library");
});

test("the wind tunnel opens in Fly it, from whichever way the air comes, and isn't a run", () => {
  expect(modeOf(["fly", "tunnel", "above"])).toBe("fly");
  expect(tunnelOf(["fly", "tunnel", "above"])).toBe("above");
  expect(tunnelOf(["fly", "tunnel"])).toBe("front");
  expect(tunnelOf(["fly", "hover"])).toBeNull();
  expect(scenarioOf(["fly", "tunnel", "above"])).toBe("hover"); // no run plays
  expect(setupOf(["fly", "tunnel", "above"])).toBeNull(); // the direction isn't a combination
  expect(tunnelLink("from behind")).toBe("#/fly/tunnel/from%20behind");
});
