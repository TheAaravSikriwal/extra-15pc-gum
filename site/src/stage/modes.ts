// Which view the route asks for. The home is inside the drone (the blueprint), #/fly/<scenario>
// is the drone flying in white space, #/fly/tunnel/<direction> the wind tunnel's flow around it
// there, and everything else is a page that opens over the view.

export type Mode = "inside" | "fly" | "page";

// the old 3D page's address still opens the drone, now the home
const INSIDE = new Set(["", "drone"]);

export function modeOf(route: string[]): Mode {
  const first = route[0] ?? "";
  if (INSIDE.has(first)) return "inside";
  if (first === "fly") return "fly";
  return "page";
}

export const DEFAULT_SCENARIO = "hover";

// a page's name for the bar along its top: the menu's (the catalog's old address is the parts page now)
export function pageName(route: string[]): string {
  const first = route[0] === "catalog" ? "parts" : (route[0] ?? "");
  return MENU.find((p) => p.route === first)?.name ?? "";
}

export function scenarioOf(route: string[]): string {
  return route[0] === "fly" && route[1] && route[1] !== "tunnel" ? route[1] : DEFAULT_SCENARIO;
}

// #/fly/<scenario>/<setup>, from a run's own page, says which combination to fly it in
export function setupOf(route: string[]): string | null {
  return route[0] === "fly" && route[1] !== "tunnel" && route[2] ? route[2] : null;
}

// where the air comes from, when the wind tunnel's flow is showing: #/fly/tunnel/<direction>
export function tunnelOf(route: string[]): string | null {
  return route[0] === "fly" && route[1] === "tunnel" ? (route[2] ?? "front") : null;
}

export function tunnelLink(direction: string): string {
  return `#/fly/tunnel/${encodeURIComponent(direction)}`;
}

export function flyLink(scenario: string, setup?: string): string {
  return `#/fly/${encodeURIComponent(scenario)}${setup ? `/${encodeURIComponent(setup)}` : ""}`;
}

// the docs, in the corner menu, grouped like a manual: the drone itself, how it was tested, the
// work that made it, and the reference behind it all
export const MENU_GROUPS: { name: string; pages: { route: string; name: string }[] }[] = [
  {
    name: "The drone",
    pages: [
      { route: "overview", name: "Overview" },
      { route: "spec", name: "Spec sheet" },
      { route: "parts", name: "Parts" },
      { route: "wiring", name: "Wiring" },
    ],
  },
  {
    name: "Tested",
    pages: [
      { route: "flights", name: "Flights" },
      { route: "tunnel", name: "Wind tunnel" },
      { route: "unproven", name: "What it can't prove" },
    ],
  },
  {
    name: "The work",
    pages: [
      { route: "steps", name: "Steps" },
      { route: "build", name: "Build it" },
    ],
  },
  {
    name: "Reference",
    pages: [
      { route: "library", name: "Library" },
      { route: "data", name: "Data" },
      { route: "math", name: "The math" },
    ],
  },
];

export const MENU: { route: string; name: string }[] = MENU_GROUPS.flatMap((g) => g.pages);
