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

export interface FlightEvent {
  at: number; // s into the run
  name: string;
}

export interface FindingRow {
  check: string;
  passed: boolean;
  detail: string;
}

export interface Playback {
  schema_version: number;
  scenario: string;
  setup: string;
  firmware: string; // px4 or mine
  passed: boolean;
  findings: FindingRow[];
  t: number[];
  position: number[][]; // m, east, north, up
  attitude: number[][]; // quaternions x, y, z, w, the body (forward-left-up) to east-north-up
  motors: number[][]; // rad/s
  events: FlightEvent[];
}

export interface Run {
  scenario: string;
  setup: string;
  firmware: string;
  flown: boolean;
  passed: boolean;
  file?: string | null;
}

export interface Flights {
  schema_version: number;
  scenarios: string[];
  setups: string[];
  runs: Run[];
}

export interface Link {
  text: string;
  url: string;
}

export interface LogEntry {
  title: string;
  date: string;
  url: string;
}

export interface StepPart {
  name: string;
  what: string;
  status: string;
  outcome: string;
}

export interface Step {
  id: string;
  number: string;
  name: string;
  purpose: string;
  status: string;
  outcome: string;
  links: Link[];
  side_track: boolean;
  report?: { verdict?: string | null; generated?: string | null; url: string } | null;
  stills: string[];
  logs: LogEntry[];
  parts: StepPart[];
}

export interface Steps {
  schema_version: number;
  steps: Step[];
}

export interface TunnelStill {
  case: string;
  view: string;
  title: string;
  subtitle: string;
  number: string;
  caption: string;
  file: string;
}

export interface TunnelFrame {
  step: number; // FluidX3D's time step
  t_s: number; // s into the run
  files: Record<string, string>; // {view: file under the data folder}
}

export interface TunnelCase {
  name: string;
  label: string;
  frames: TunnelFrame[];
}

export interface Tunnel {
  schema_version: number;
  fork_public: boolean;
  note: string;
  stills: TunnelStill[];
  cases: TunnelCase[];
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
  Playback: [
    "schema_version",
    "scenario",
    "setup",
    "firmware",
    "passed",
    "findings",
    "t",
    "position",
    "attitude",
    "motors",
    "events",
  ],
  Run: ["scenario", "setup", "firmware", "flown", "passed", "file"],
  Flights: ["schema_version", "scenarios", "setups", "runs"],
  Step: [
    "id",
    "number",
    "name",
    "purpose",
    "status",
    "outcome",
    "links",
    "side_track",
    "report",
    "stills",
    "logs",
    "parts",
  ],
  Steps: ["schema_version", "steps"],
  TunnelStill: ["case", "view", "title", "subtitle", "number", "caption", "file"],
  TunnelFrame: ["step", "t_s", "files"],
  TunnelCase: ["name", "label", "frames"],
  Tunnel: ["schema_version", "fork_public", "note", "stills", "cases"],
} as const;
