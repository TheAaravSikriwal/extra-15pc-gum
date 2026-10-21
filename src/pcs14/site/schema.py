"""The shapes of the site's data files, as pydantic models.

These are the one definition: `pcs14 site` builds its files through them, the tests read the
files back through them, and `pcs14 site --schema` exports them as JSON Schema into site/schema,
which the site's TypeScript types follow. A file carries the schema version it was written
with, and the site refuses one from another version.
"""

from typing import Any

from pydantic import BaseModel, ConfigDict

SCHEMA_VERSION = 1


class _Shape(BaseModel):
    model_config = ConfigDict(extra="forbid")


class ReportFound(_Shape):
    file: str  # where it was looked for, relative to the reports folder
    found: bool
    generated: str | None = None  # the report's own date
    verdict: str | None = None


class Index(_Shape):
    """index.json: what was made, from which commit and which reports."""

    schema_version: int
    generated: str
    commit: str | None
    reports: dict[str, ReportFound]
    files: list[str]  # the other data files written, next to this one


class Check(_Shape):
    name: str
    unit: str
    nominal: float
    pessimistic: float | None = None
    limit: float | None = None
    higher_is_better: bool = True
    verdict: str
    note: str = ""


class Combination(_Shape):
    name: str
    modules: list[str]
    verdict: str
    mass_g: float  # the sizing model's, with its growth margin
    growth_margin_g: float
    cad_mass_g: float | None = None  # the CAD's, without the margin
    center_of_gravity_mm: list[float] | None = None
    checks: list[Check]
    top_speed_kmh: dict[str, float]  # at a full pack, half and the reserve
    least_power_speed_ms: float
    least_power_minutes: float


class Part(_Shape):
    role: str  # motor, prop, esc, frame, cell, or a component's id
    module: str | None = None  # None for Base
    id: str
    maker: str
    model: str
    mass_g: float
    price_usd: float | None = None
    link: str | None = None
    count: int = 1


class SpecSheet(_Shape):
    """spec.json: the live spec sheet, per combination."""

    schema_version: int
    sizing_case: str
    verdict: str
    targets: dict[str, float]
    combinations: list[Combination]
    parts: list[Part]


class Piece(_Shape):
    name: str  # the GLB's node for it
    kind: str  # frame, motor, prop, pack, bought, printed or wire
    module: str  # base, V, P or C
    mass_g: float
    part_id: str | None = None
    moving: bool = False
    catalog: Part | None = None  # the spec sheet's entry, for a bought part


class Parts(_Shape):
    """parts.json: every piece of the full drone, for the 3D explorer's cards."""

    schema_version: int
    glb: str  # the model the names belong to
    pieces: list[Piece]


class Wire(_Shape):
    label: str  # the connection list's, "board.connector.pin to board.connector.pin"
    ends: list[str]  # its two pins


class Route(_Shape):
    name: str  # as the CAD's settings name it
    node: str  # the GLB's node for it
    wires: list[Wire]
    heating_share: dict[str, dict[str, float]]  # combination, then case: the hardest wire's


class Wires(_Shape):
    """wires.json: the CAD's wire routes, what runs along each and how hard it works."""

    schema_version: int
    routes: list[Route]


class WireEnd3d(_Shape):
    pin: str  # BOARD.CONNECTOR.PIN, the connection list's name for it
    at_mm: list[float]  # in the drone's frame, the CAD's (z up)
    piece: str  # the model's piece it rides with when the drone is pulled apart


class Wire3d(_Shape):
    label: str
    harness: str
    ends: list[WireEnd3d]  # two
    route: str | None  # its CAD route, or None for a short jumper
    route_piece: str | None  # the model's piece for that route
    path_mm: list[list[float]]  # the route's points from the first end's side, or none
    awg: int
    diameter_mm: float  # over its insulation, from the wire's gauge table
    wire: str  # its type, in words
    role: str  # what its first pin carries: power, ground, signal or bus
    length_mm: float  # plug to plug along its route, or a jumper's own: what to cut it to
    # how far each end's plug is from where it joins its route: the rough routes to redraw
    gaps_mm: list[float]


class PinSource(_Shape):
    connector: str  # BOARD.CONNECTOR
    part_id: str
    estimate: bool
    url: str | None
    note: str | None


class Wires3d(_Shape):
    """wires3d.json: every wire pin to pin in the drone's frame, and where the pins came from."""

    schema_version: int
    wires: list[Wire3d]
    connectors: list[PinSource]


class Event(_Shape):
    at: float  # s into the log
    name: str


class FindingRow(_Shape):
    check: str
    passed: bool
    detail: str


class Playback(_Shape):
    """flights/<setup>-<scenario>-<firmware>.json: one run, for the site to play back."""

    schema_version: int
    scenario: str
    setup: str
    firmware: str  # px4 or mine
    passed: bool
    findings: list[FindingRow]
    t: list[float]  # s
    position: list[list[float]]  # m, east, north, up, from Gazebo's ground truth
    attitude: list[list[float]]  # quaternions x, y, z, w: the body (forward-left-up) to it
    motors: list[list[float]]  # rad/s, each motor
    events: list[Event]


class Run(_Shape):
    scenario: str
    setup: str
    firmware: str
    flown: bool
    passed: bool
    file: str | None = None  # its playback file, when its log is there


class ScenarioAbout(_Shape):
    name: str
    step: int  # the step that flew it first: 4 (both firmwares), 6 or 7 (mine)
    what: str  # what it tests, in a line


class Flights(_Shape):
    """flights.json: every run of both firmwares, for the matrices and the playback pages."""

    schema_version: int
    scenarios: list[str]
    about: list[ScenarioAbout]
    setups: list[str]
    runs: list[Run]


class Link(_Shape):
    text: str
    url: str


class LogEntry(_Shape):
    title: str
    date: str
    url: str


class ReportRef(_Shape):
    verdict: str | None = None
    generated: str | None = None
    url: str


class StepPart(_Shape):
    name: str  # "5c. Build"
    what: str
    status: str
    outcome: str


class Step(_Shape):
    id: str
    number: str  # "1" to "8", or "" for a side track
    name: str
    purpose: str
    status: str
    outcome: str  # the README's, with its links as plain words
    links: list[Link]
    side_track: bool
    report: ReportRef | None = None
    stills: list[str]  # under the data folder
    logs: list[LogEntry]
    parts: list[StepPart] = []  # the README's "in detail" rows: its talk, plan, build
    learning: list[Link] = []  # its topics in docs/learning.md


class Steps(_Shape):
    """steps.json: a page per step, from the README's plan, the reports and the log."""

    schema_version: int
    steps: list[Step]


class TunnelStill(_Shape):
    case: str  # "Max-cruise"
    view: str  # FluidX3D's frame name
    title: str
    subtitle: str
    number: str
    caption: str
    file: str  # under the data folder


class TunnelFrame(_Shape):
    step: int  # FluidX3D's time step
    t_s: float  # s into the run
    files: dict[str, str]  # {view: file under the data folder}


class TunnelCase(_Shape):
    name: str
    label: str  # "Cruise"
    frames: list[TunnelFrame]


class Tunnel(_Shape):
    """tunnel.json: the wind tunnel's stills and each case's frames along the way."""

    schema_version: int
    fork_public: bool  # until FluidX3D's fork is public, these stay off the public site
    note: str
    stills: list[TunnelStill]
    cases: list[TunnelCase]


class PinRow(_Shape):
    pin: str  # CONNECTOR.PIN
    role: str  # power, ground, in, out, both
    functions: str  # what PX4 or the chip calls it
    to: str  # the pins it joins
    harness: str


class BoardPins(_Shape):
    name: str  # the connection list's
    part: str
    module: str
    pins: list[PinRow]


class Harness(_Shape):
    name: str
    file: str  # under the data folder


class Wiring(_Shape):
    """wiring.json: every board's pins, the harness diagrams and the schematic."""

    schema_version: int
    boards: list[BoardPins]
    harnesses: list[Harness]
    schematic: str | None = None  # under the data folder, when the electrical run drew it
    kicad: str  # the schematic's KiCad file, on GitHub


class UnprovenItem(_Shape):
    what: str
    measure: str = ""  # the first thing to measure once it's built, where that's written


class UnprovenGroup(_Shape):
    name: str  # "The whole drone", or a report's step
    url: str  # where it's written
    items: list[UnprovenItem]


class Unproven(_Shape):
    """unproven.json: what the sims can't prove, front and center."""

    schema_version: int
    groups: list[UnprovenGroup]


class BuildLine(_Shape):
    module: str  # base, V, P, C, or "once"
    group: str  # bought, wire, plug, hardware, printed, ground, supplies, tools, spares
    name: str
    qty: float
    unit: str
    maker: str
    model: str
    link: str | None = None
    price_each_usd: float | None = None
    total_usd: float | None = None
    checked: str | None = None
    fallback: str
    note: str


class BuildTotal(_Shape):
    setup: str  # a combination, or "once"
    usd: float  # of the priced lines
    unpriced: int
    printed: int
    printed_g: float


class BuildGuide(_Shape):
    name: str
    url: str


class Build(_Shape):
    """build.json: the build package's parts list, its totals and its guides."""

    schema_version: int
    generated: str
    totals: list[BuildTotal]
    lines: list[BuildLine]
    guides: list[BuildGuide]
    open: list[str]


class LibraryDoc(_Shape):
    path: str  # the repo path without .md, which is its route: #/library/<path>
    title: str
    section: str
    url: str  # on GitHub
    date: str | None = None  # from a dated file's name


class LibrarySection(_Shape):
    name: str
    docs: list[LibraryDoc]


class Library(_Shape):
    """library.json: every Markdown doc in the repo, by section."""

    schema_version: int
    sections: list[LibrarySection]


class LibraryPage(_Shape):
    """library/<path>.json: one doc, rendered."""

    schema_version: int
    path: str
    title: str
    url: str
    html: str


class CatalogPart(_Shape):
    id: str
    type: str
    maker: str
    model: str
    mass_g: float | None = None
    price_usd: float | None = None
    link: str | None = None
    record: dict[str, Any]  # every field the catalog has for it


class Catalog(_Shape):
    """catalog.json: every part in the catalog, every field."""

    schema_version: int
    parts: list[CatalogPart]


class RawFile(_Shape):
    name: str
    title: str
    source: str  # the repo path
    url: str


class RawIndex(_Shape):
    """raw.json: the reports' own data files, copied whole under raw/."""

    schema_version: int
    files: list[RawFile]


class RawData(_Shape):
    """raw/<name>.json: one report's data file, whole."""

    schema_version: int
    name: str
    source: str
    data: Any


class MathItem(_Shape):
    name: str
    kind: str  # function, class or method
    signature: str
    doc: str
    line: int


class MathModule(_Shape):
    path: str
    language: str
    doc: str
    url: str
    items: list[MathItem]


class MathPackage(_Shape):
    name: str
    key: str
    modules: list[MathModule]


class Math(_Shape):
    """math.json: how each number is worked out, from the code's own explanations."""

    schema_version: int
    packages: list[MathPackage]


# each data file's name (without .json) and its shape
FILES: dict[str, type[_Shape]] = {
    "index": Index,
    "spec": SpecSheet,
    "parts": Parts,
    "wires": Wires,
    "wires3d": Wires3d,
    "flights": Flights,
    "playback": Playback,
    "steps": Steps,
    "tunnel": Tunnel,
    "unproven": Unproven,
    "wiring": Wiring,
    "build": Build,
    "library": Library,
    "library-page": LibraryPage,
    "catalog": Catalog,
    "raw": RawIndex,
    "raw-data": RawData,
    "math": Math,
}
