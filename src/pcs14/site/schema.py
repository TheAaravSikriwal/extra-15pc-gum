"""The shapes of the site's data files, as pydantic models.

These are the one definition: `pcs14 site` builds its files through them, the tests read the
files back through them, and `pcs14 site --schema` exports them as JSON Schema into site/schema,
which the site's TypeScript types follow. A file carries the schema version it was written
with, and the site refuses one from another version.
"""

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


# each data file's name (without .json) and its shape
FILES: dict[str, type[_Shape]] = {
    "index": Index,
    "spec": SpecSheet,
    "parts": Parts,
    "wires": Wires,
}
