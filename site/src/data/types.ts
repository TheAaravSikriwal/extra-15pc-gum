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
  // as the sizing report prints them, rounded toward failing
  shown: string;
  shown_pessimistic?: string | null;
  shown_limit?: string | null; // "at least 25.0 min"
  shown_margin?: string | null; // "+58%"
}

export interface MassLine {
  name: string;
  grams: number;
  group: string; // base, a module, payload or margin
}

// how the CAD balances a combination
export interface Balance {
  passed: boolean;
  trim_x_mm: number; // where the pack slides to
  center_of_gravity_mm: number[];
  busiest_motor_extra: number; // a share: 0.002 is 0.2% harder than the others
  inertia_kg_m2: number[][];
}

export interface Combination {
  name: string;
  modules: string[];
  verdict: string;
  required: boolean;
  mass_g: number;
  growth_margin_g: number;
  cad_mass_g?: number | null;
  center_of_gravity_mm?: number[] | null;
  checks: Check[];
  top_speed_kmh: Record<string, number>;
  least_power_speed_ms: number;
  least_power_minutes: number;
  mass_lines: MassLine[]; // what the sizing model's weight is made of
  balance?: Balance | null;
  numbers: string[][]; // [what, its value] as the sizing report words it
}

export interface Pack {
  cell: string;
  cell_id: string;
  series: number;
  parallel: number;
  capacity_mah: number;
  resistance_mohm: number;
  mass_g: number;
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
  pack?: Pack | null;
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

// every wire pin to pin, in the drone's frame (the CAD's, mm, z up)
export interface WireEnd3d {
  pin: string; // BOARD.CONNECTOR.PIN
  at_mm: number[];
  piece: string; // the model's piece it rides with when pulled apart
}

export interface Wire3d {
  label: string;
  harness: string;
  ends: WireEnd3d[];
  route: string | null;
  route_piece: string | null;
  path_mm: number[][]; // the route's points from the first end's side
  awg: number;
  diameter_mm: number;
  wire: string;
  role: string; // power, ground, signal or bus
  length_mm: number;
  gaps_mm: number[]; // each end's plug to where it joins its route
}

export interface PinSource {
  connector: string; // BOARD.CONNECTOR
  part_id: string;
  estimate: boolean;
  url: string | null;
  note: string | null;
}

export interface Wires3d {
  schema_version: number;
  wires: Wire3d[];
  connectors: PinSource[];
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

// a run's own shape for the scenario list: its path from above, or its height over time (0 to 1, y up)
export interface Glyph {
  kind: string; // plan or profile
  points: number[][];
}

export interface Run {
  scenario: string;
  setup: string;
  firmware: string;
  flown: boolean;
  passed: boolean;
  file?: string | null;
  glyph?: Glyph | null;
  missed?: string | null; // a failed run's first failed check, "check: detail"
}

export interface ScenarioAbout {
  name: string;
  step: number; // the step that flew it first: 4 (both firmwares), 6 or 7 (mine)
  what: string;
}

export interface Flights {
  schema_version: number;
  scenarios: string[];
  about: ScenarioAbout[];
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
  learning: Link[];
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
  label: string; // "From the front", as the drone view names it
  frames: TunnelFrame[];
  direction: string;
  about: string;
  grid?: string | null; // FluidX3D's cells, "352 x 804 x 276"
  cell_mm?: number | null;
  steps?: number | null;
  air_s?: number | null; // seconds of air simulated
  box_m?: number[] | null; // across, along the wind, up
  force_n?: number | null; // along the wind, visual-grade
}

// a case's flow moving, around the drone in its own frame (x forward, y left, z up, m): particles
// carried through it, and the speed on a slice through the drone, a loop's frames of each
export interface TunnelParticles {
  file: string; // bytes, as pcs14.aero.motion.particle_bytes packs them
  count: number;
}

export interface TunnelSlice {
  file: string; // bytes: each frame's speed, a share of color_max, a pixel, the first row on top
  width: number;
  height: number;
  corners: number[][]; // m in the drone's frame: top left, top right, bottom right, bottom left
}

export interface TunnelFlow {
  schema_version: number;
  name: string;
  direction: string; // where the air comes from: front, back, right, left, above, below or hover
  setup: string;
  speed: number; // m/s, the wind (0 in the hover)
  color_max: number; // m/s at the top of the colors
  force_n: number | null; // N along the wind: FluidX3D's own number, visual-grade
  pitch_deg: number; // nose down, the way it flies into this air
  loop_s: number; // s of the air's time a loop plays
  frames: number; // a loop's frames
  particles: TunnelParticles;
  slice: TunnelSlice;
}

export interface TunnelFlowEntry {
  name: string;
  direction: string;
  label: string; // "From the front"
  about: string;
  file?: string | null; // its TunnelFlow, under the data folder; none while it's not run yet
}

export interface Tunnel {
  schema_version: number;
  fork_public: boolean;
  note: string;
  stills: TunnelStill[];
  cases: TunnelCase[];
  flows?: TunnelFlowEntry[];
}

export interface PinRow {
  pin: string;
  role: string;
  functions: string;
  to: string;
  harness: string;
}

export interface BoardPins {
  name: string;
  part: string;
  module: string;
  pins: PinRow[];
}

export interface Harness {
  name: string;
  file: string;
}

export interface Wiring {
  schema_version: number;
  boards: BoardPins[];
  harnesses: Harness[];
  schematic?: string | null;
  kicad: string;
}

export interface UnprovenItem {
  what: string;
  measure: string;
}

export interface UnprovenGroup {
  name: string;
  url: string; // where it's written, in the site's library
  items: UnprovenItem[];
  step?: string | null; // its step's id
}

export interface Unproven {
  schema_version: number;
  groups: UnprovenGroup[];
}

export interface BuildLine {
  module: string;
  group: string;
  name: string;
  qty: number;
  unit: string;
  maker: string;
  model: string;
  link?: string | null;
  price_each_usd?: number | null;
  total_usd?: number | null;
  checked?: string | null;
  fallback: string;
  note: string;
}

export interface BuildTotal {
  setup: string;
  usd: number;
  unpriced: number;
  printed: number;
  printed_g: number;
}

export interface BuildGuide {
  name: string;
  url: string; // its page in the library
  about: string;
}

export interface Build {
  schema_version: number;
  generated: string;
  totals: BuildTotal[];
  lines: BuildLine[];
  guides: BuildGuide[];
  open: string[];
}

export interface LibraryDoc {
  path: string;
  title: string;
  section: string;
  url: string;
  date?: string | null;
}

export interface LibrarySection {
  name: string;
  docs: LibraryDoc[];
}

export interface Library {
  schema_version: number;
  sections: LibrarySection[];
}

export interface LibraryPage {
  schema_version: number;
  path: string;
  title: string;
  url: string;
  html: string;
}

export interface CatalogPart {
  id: string;
  type: string;
  maker: string;
  model: string;
  mass_g?: number | null;
  price_usd?: number | null;
  link?: string | null;
  record: Record<string, unknown>;
}

export interface Catalog {
  schema_version: number;
  parts: CatalogPart[];
}

// what goes on the drone, from the build package, each line with its catalog entry
export interface PartsLine {
  module: string; // base, V, P, C, or "once"
  group: string; // bought, wire, plug, hardware, printed, ground, supplies, tools, spares
  name: string;
  qty: number;
  unit: string;
  maker: string;
  model: string;
  link?: string | null;
  price_each_usd?: number | null;
  total_usd?: number | null;
  checked?: string | null;
  fallback: string; // Markdown, its links kept
  note: string;
  catalog_id?: string | null;
  mass_g?: number | null; // each, from the catalog
}

export interface PartsList {
  schema_version: number;
  generated: string;
  lines: PartsLine[];
  used: CatalogPart[]; // the catalog entries the design uses
  alternatives: CatalogPart[]; // the rest of the catalog
}

export interface RawFile {
  name: string;
  title: string;
  source: string;
  url: string;
}

export interface RawIndex {
  schema_version: number;
  files: RawFile[];
}

export interface RawData {
  schema_version: number;
  name: string;
  source: string;
  data: unknown;
}

export interface MathItem {
  name: string;
  kind: string;
  signature: string;
  doc: string;
  line: number;
}

export interface MathModule {
  path: string;
  language: string;
  doc: string;
  url: string;
  items: MathItem[];
}

export interface MathPackage {
  name: string;
  key: string;
  modules: MathModule[];
}

export interface MathData {
  schema_version: number;
  packages: MathPackage[];
}

// the fields each shape has, for the check against the schema
export const FIELDS = {
  ReportFound: ["file", "found", "generated", "verdict"],
  Index: ["schema_version", "generated", "commit", "reports", "files"],
  Check: [
    "name",
    "unit",
    "nominal",
    "pessimistic",
    "limit",
    "higher_is_better",
    "verdict",
    "note",
    "shown",
    "shown_pessimistic",
    "shown_limit",
    "shown_margin",
  ],
  MassLine: ["name", "grams", "group"],
  Balance: ["passed", "trim_x_mm", "center_of_gravity_mm", "busiest_motor_extra", "inertia_kg_m2"],
  Pack: ["cell", "cell_id", "series", "parallel", "capacity_mah", "resistance_mohm", "mass_g"],
  Combination: [
    "name",
    "modules",
    "verdict",
    "required",
    "mass_g",
    "growth_margin_g",
    "cad_mass_g",
    "center_of_gravity_mm",
    "checks",
    "top_speed_kmh",
    "least_power_speed_ms",
    "least_power_minutes",
    "mass_lines",
    "balance",
    "numbers",
  ],
  Part: ["role", "module", "id", "maker", "model", "mass_g", "price_usd", "link", "count"],
  SpecSheet: ["schema_version", "sizing_case", "verdict", "targets", "combinations", "parts", "pack"],
  Piece: ["name", "kind", "module", "mass_g", "part_id", "moving", "catalog"],
  Parts: ["schema_version", "glb", "pieces"],
  Wire: ["label", "ends"],
  Route: ["name", "node", "wires", "heating_share"],
  Wires: ["schema_version", "routes"],
  WireEnd3d: ["pin", "at_mm", "piece"],
  Wire3d: ["label", "harness", "ends", "route", "route_piece", "path_mm", "awg", "diameter_mm", "wire", "role", "length_mm", "gaps_mm"],
  PinSource: ["connector", "part_id", "estimate", "url", "note"],
  Wires3d: ["schema_version", "wires", "connectors"],
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
  Glyph: ["kind", "points"],
  Run: ["scenario", "setup", "firmware", "flown", "passed", "file", "glyph", "missed"],
  ScenarioAbout: ["name", "step", "what"],
  Flights: ["schema_version", "scenarios", "about", "setups", "runs"],
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
    "learning",
  ],
  Steps: ["schema_version", "steps"],
  TunnelStill: ["case", "view", "title", "subtitle", "number", "caption", "file"],
  TunnelFrame: ["step", "t_s", "files"],
  TunnelCase: ["name", "label", "frames", "direction", "about", "grid", "cell_mm", "steps", "air_s", "box_m", "force_n"],
  TunnelParticles: ["file", "count"],
  TunnelSlice: ["file", "width", "height", "corners"],
  TunnelFlow: ["schema_version", "name", "direction", "setup", "speed", "color_max", "force_n", "pitch_deg", "loop_s", "frames", "particles", "slice"],
  TunnelFlowEntry: ["name", "direction", "label", "about", "file"],
  Tunnel: ["schema_version", "fork_public", "note", "stills", "cases", "flows"],
  UnprovenItem: ["what", "measure"],
  UnprovenGroup: ["name", "url", "items", "step"],
  Unproven: ["schema_version", "groups"],
  PinRow: ["pin", "role", "functions", "to", "harness"],
  BoardPins: ["name", "part", "module", "pins"],
  Harness: ["name", "file"],
  Wiring: ["schema_version", "boards", "harnesses", "schematic", "kicad"],
  BuildLine: [
    "module",
    "group",
    "name",
    "qty",
    "unit",
    "maker",
    "model",
    "link",
    "price_each_usd",
    "total_usd",
    "checked",
    "fallback",
    "note",
  ],
  BuildTotal: ["setup", "usd", "unpriced", "printed", "printed_g"],
  BuildGuide: ["name", "url", "about"],
  Build: ["schema_version", "generated", "totals", "lines", "guides", "open"],
  LibraryDoc: ["path", "title", "section", "url", "date"],
  LibrarySection: ["name", "docs"],
  Library: ["schema_version", "sections"],
  LibraryPage: ["schema_version", "path", "title", "url", "html"],
  CatalogPart: ["id", "type", "maker", "model", "mass_g", "price_usd", "link", "record"],
  Catalog: ["schema_version", "parts"],
  PartsLine: [
    "module",
    "group",
    "name",
    "qty",
    "unit",
    "maker",
    "model",
    "link",
    "price_each_usd",
    "total_usd",
    "checked",
    "fallback",
    "note",
    "catalog_id",
    "mass_g",
  ],
  PartsList: ["schema_version", "generated", "lines", "used", "alternatives"],
  RawFile: ["name", "title", "source", "url"],
  RawIndex: ["schema_version", "files"],
  RawData: ["schema_version", "name", "source", "data"],
  MathItem: ["name", "kind", "signature", "doc", "line"],
  MathModule: ["path", "language", "doc", "url", "items"],
  MathPackage: ["name", "key", "modules"],
  Math: ["schema_version", "packages"],
} as const;
