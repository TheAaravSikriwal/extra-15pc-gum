"""design/electrical.yaml as objects: the boards, the wires, what plugs into what, and the
check numbers.

Pins are named BOARD.CONNECTOR.PIN, with the board's short name from this file and the
connector and pin from the part's catalog block (`fc.CAN.CAN_P`). The battery is the board
`pack`, with the pins `pack.XT60.+` and `pack.XT60.-`. Lengths are in millimeters here, like
everything people edit, and the properties hand them back in meters.
"""

from pathlib import Path
from typing import Literal

import yaml
from pydantic import Field, ValidationError, model_validator

from pcs14 import units
from pcs14.catalog.source import Strict
from pcs14.design import _explain

Module = Literal["base", "V", "P", "C"]
PACK = "pack"


class ElectricalError(Exception):
    """design/electrical.yaml is broken."""


class Board(Strict):
    part: str
    module: Module | None = None  # where it sits, when the build lists its part in more than one
    modes: dict[str, Literal["in", "out", "both"]] = Field(
        default_factory=dict
    )  # how pins are used
    terminator: bool | None = None  # a CAN node's own switchable terminator


class WireRun(Strict):
    ends: tuple[str, str]
    wire: str  # a wire table in the catalog
    awg: int
    route: str | None = None  # a wire route in design/cad.yaml
    length_mm: float | None = Field(default=None, gt=0)  # for short runs without a route
    harness: str
    name: str | None = None

    @property
    def label(self) -> str:
        return self.name or f"{self.ends[0]} to {self.ends[1]}"

    @property
    def length(self) -> float | None:
        return None if self.length_mm is None else units.mm_to_m(self.length_mm)


class Mate(Strict):
    """Two connectors plugged together: their pins join by name."""

    a: str  # BOARD.CONNECTOR
    b: str


class Link(Strict):
    """Pins joined with no wire of their own: a HAT on a header, a ribbon, a board soldered on."""

    name: str
    pins: list[str] = Field(min_length=2)


class Requirement(Strict):
    """Pins that have to share a net whenever their boards are fitted: the safety design's
    paths, written down so a wire can't go missing quietly."""

    name: str
    pins: list[str] = Field(min_length=2)


class FuseChoice(Strict):
    element: str  # BOARD.ELEMENT
    family: str
    rated_a: float = Field(gt=0)


class CellLinks(Strict):
    """The fuse links between each cell and its busbar."""

    wire: str
    awg: int
    length_mm: float = Field(gt=0)
    joint_max_c: float  # the hottest the joint on the cell can get


class CheckNumbers(Strict):
    """The spec's check numbers (docs/specs/2026-10-18-electrical.md)."""

    continuous_share: float = Field(gt=0, le=1)  # of a continuous rating
    burst_s: float = Field(gt=0)  # at the current cap
    air_c: float
    temp_margin_c: float = Field(ge=0)  # under every rated maximum
    main_drop_share: float = Field(gt=0, lt=1)  # of the pack's nominal voltage, at the cap
    load_margin_v: float = Field(ge=0)  # inside every load's range, at both ends
    pin_minimums: dict[str, float] = Field(default_factory=dict)  # firmer floors, like the Pi's
    # ceilings checked without the margin, for a part whose maker publishes no maximum (the
    # reason goes on the unproven list)
    pin_ceilings: dict[str, float] = Field(default_factory=dict)
    # connectors (board.CONNECTOR) whose heat my firmware limits by easing the current cap
    heat_limited: list[str] = Field(default_factory=list)
    supply_typical_share: float = Field(gt=0, le=1)  # of a supply's continuous rating
    fuse_hold_factor: float = Field(ge=1)
    cell_link_blow_s: float = Field(gt=0)  # a dead short melts the link this fast
    backups: list[str] = Field(default_factory=list)  # supplies to switch off, one at a time
    rise_share: float = Field(gt=0, lt=1)  # of a bit
    threshold_margin_share: float = Field(ge=0, lt=1)  # of the supply


class ConnectionList(Strict):
    boards: dict[str, Board]
    wires: list[WireRun]
    mates: list[Mate] = Field(default_factory=list)
    links: list[Link] = Field(default_factory=list)
    fuses: list[FuseChoice] = Field(default_factory=list)
    requires: list[Requirement] = Field(default_factory=list)
    cell_links: CellLinks | None = None
    unproven: list[str] = Field(default_factory=list)  # what the design knowingly doesn't cover
    checks: CheckNumbers | None = None

    @model_validator(mode="after")
    def _names(self):
        if PACK in self.boards:
            raise ValueError(f"'{PACK}' is the battery's name; give the board another")
        bad = [name for name in self.boards if "." in name]
        if bad:
            raise ValueError(f"board names can't have dots in them: {', '.join(bad)}")
        return self


def load_connection_list(path: Path) -> ConnectionList:
    path = Path(path)
    try:
        data = yaml.safe_load(path.read_text(encoding="utf-8"))
    except (OSError, yaml.YAMLError) as error:
        raise ElectricalError(f"{path.name}: can't read it ({error})") from error
    try:
        return ConnectionList.model_validate(data)
    except ValidationError as error:
        raise ElectricalError(f"{path.name}: " + _explain(error)) from None
