// Which view the route asks for. The home is inside the drone (the blueprint), #/fly/<scenario>
// is the drone flying in white space, and everything else is a page that opens over the view.

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

export function scenarioOf(route: string[]): string {
  return route[0] === "fly" && route[1] ? route[1] : DEFAULT_SCENARIO;
}

// the other pages, in the corner menu; the drone in 3D and the wiring are the view itself now
export const MENU: { route: string; name: string }[] = [
  { route: "spec", name: "Spec sheet" },
  { route: "flights", name: "Every flight" },
  { route: "steps", name: "Every step" },
  { route: "tunnel", name: "The wind tunnel" },
  { route: "unproven", name: "What it can't prove" },
  { route: "build", name: "Build it" },
  { route: "library", name: "The library" },
  { route: "catalog", name: "The catalog" },
  { route: "data", name: "The data" },
  { route: "math", name: "The math" },
];
