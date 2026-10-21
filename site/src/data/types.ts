// The data files' shapes, as site/schema exports them from pcs14.site.schema. types.test.ts
// checks these field lists against the schema files, so the two can't drift.

export const SCHEMA_VERSION = 1;

export interface ReportFound {
  file: string;
  found: boolean;
  generated?: string | null;
  verdict?: string | null;
}

export interface Index {
  schema_version: number;
  generated: string;
  commit: string | null;
  reports: Record<string, ReportFound>;
  files: string[];
}

export interface Check {
  name: string;
  unit: string;
  nominal: number;
  pessimistic?: number | null;
  limit?: number | null;
  higher_is_better: boolean;
  verdict: string;
  note: string;
}

export interface Combination {
  name: string;
  modules: string[];
  verdict: string;
  mass_g: number;
  growth_margin_g: number;
  cad_mass_g?: number | null;
  center_of_gravity_mm?: number[] | null;
  checks: Check[];
  top_speed_kmh: Record<string, number>;
  least_power_speed_ms: number;
  least_power_minutes: number;
}

export interface Part {
  role: string;
  module?: string | null;
  id: string;
  maker: string;
  model: string;
  mass_g: number;
  price_usd?: number | null;
  link?: string | null;
  count: number;
}

export interface SpecSheet {
  schema_version: number;
  sizing_case: string;
  verdict: string;
  targets: Record<string, number>;
  combinations: Combination[];
  parts: Part[];
}

export interface Piece {
  name: string; // the GLB's node for it
  kind: string; // frame, motor, prop, pack, bought, printed or wire
  module: string; // base, V, P or C
  mass_g: number;
  part_id?: string | null;
  moving: boolean;
  catalog?: Part | null;
}

export interface Parts {
  schema_version: number;
  glb: string;
  pieces: Piece[];
}

export interface Wire {
  label: string;
  ends: string[];
}

export interface Route {
  name: string;
  node: string; // the GLB's node for it
  wires: Wire[];
  heating_share: Record<string, Record<string, number>>; // combination, then case
}

export interface Wires {
  schema_version: number;
  routes: Route[];
}

// the fields each shape has, for the check against the schema
export const FIELDS = {
  ReportFound: ["file", "found", "generated", "verdict"],
  Index: ["schema_version", "generated", "commit", "reports", "files"],
  Check: ["name", "unit", "nominal", "pessimistic", "limit", "higher_is_better", "verdict", "note"],
  Combination: [
    "name",
    "modules",
    "verdict",
    "mass_g",
    "growth_margin_g",
    "cad_mass_g",
    "center_of_gravity_mm",
    "checks",
    "top_speed_kmh",
    "least_power_speed_ms",
    "least_power_minutes",
  ],
  Part: ["role", "module", "id", "maker", "model", "mass_g", "price_usd", "link", "count"],
  SpecSheet: ["schema_version", "sizing_case", "verdict", "targets", "combinations", "parts"],
  Piece: ["name", "kind", "module", "mass_g", "part_id", "moving", "catalog"],
  Parts: ["schema_version", "glb", "pieces"],
  Wire: ["label", "ends"],
  Route: ["name", "node", "wires", "heating_share"],
  Wires: ["schema_version", "routes"],
} as const;
