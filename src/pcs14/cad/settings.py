"""design/cad.yaml as objects: materials, the check limits, the layout and the wire routes.

The file is in millimeters and degrees, like everything people edit; the properties hand
lengths back in meters.
"""

from dataclasses import dataclass
from pathlib import Path
from typing import Literal

import yaml
from pydantic import Field, ValidationError, model_validator

from pcs14 import units
from pcs14.catalog.source import Strict
from pcs14.design import _explain

Point = tuple[float, float, float]


# the catalog entries holding each module's wiring, spread over its wire routes
WIRING_PARTS = {"base": "base-wiring", "V": "v-wiring", "P": "p-wiring", "C": "c-wiring"}


class SettingsError(Exception):
    """design/cad.yaml is broken."""


def _m(values) -> tuple[float, ...]:
    return tuple(units.mm_to_m(v) for v in values)


class Material(Strict):
    density_g_cm3: float = Field(gt=0)
    fill: float = Field(gt=0, le=1)  # walls plus infill, as a share of solid
    note: str

    @property
    def density(self) -> float:
        """Effective kg per cubic meter, fill included."""
        return self.density_g_cm3 * 1000 * self.fill


class Print(Strict):
    min_wall_mm: float = Field(gt=0)

    @property
    def min_wall(self) -> float:
        return units.mm_to_m(self.min_wall_mm)


class Checks(Strict):
    max_motor_overload: float = Field(gt=0)
    rigid_clearance_mm: float = Field(ge=0)
    moving_clearance_mm: float = Field(ge=0)
    chute_cone_half_angle_deg: float = Field(gt=0, lt=90)
    chute_cone_height_mm: float = Field(gt=0)
    compass_from_power_mm: float = Field(ge=0)
    remote_id_from_gps_mm: float = Field(ge=0)
    compass_part: str  # the part with the compass in it (the GPS)
    remote_id_part: str

    @property
    def rigid_clearance(self) -> float:
        return units.mm_to_m(self.rigid_clearance_mm)

    @property
    def moving_clearance(self) -> float:
        return units.mm_to_m(self.moving_clearance_mm)

    @property
    def chute_cone_height(self) -> float:
        return units.mm_to_m(self.chute_cone_height_mm)

    @property
    def compass_from_power(self) -> float:
        return units.mm_to_m(self.compass_from_power_mm)

    @property
    def remote_id_from_gps(self) -> float:
        return units.mm_to_m(self.remote_id_from_gps_mm)


class PackSettings(Strict):
    tray_max_length_mm: float = Field(gt=0)
    tray_max_width_mm: float = Field(gt=0)
    x_mm: float
    slide_mm: float = Field(ge=0)
    tray_thickness_mm: float = Field(gt=0)


class Legs(Strict):
    spots_mm: list[tuple[float, float]] = Field(min_length=3)
    diameter_mm: float = Field(gt=0)
    below_pack_mm: float = Field(ge=0)
    material: str


class Rail(Strict):
    from_x_mm: float
    to_x_mm: float
    width_mm: float = Field(gt=0)
    height_mm: float = Field(gt=0)
    material: str


class GpsMast(Strict):
    at_mm: tuple[float, float]
    height_mm: float = Field(gt=0)
    tube_diameter_mm: float = Field(gt=0)
    mount_size_mm: float = Field(gt=0)
    material: str


class VHousing(Strict):
    from_x_mm: float
    to_x_mm: float
    width_mm: float = Field(gt=0)
    height_mm: float = Field(gt=0)
    wall_mm: float = Field(gt=0)
    material: str


class PHolder(Strict):
    height_mm: float = Field(gt=0)
    wall_mm: float = Field(gt=0)
    material: str


class Placement(Strict):
    at_mm: Point
    turn_deg: Point = (0, 0, 0)

    @property
    def at(self) -> Point:
        return _m(self.at_mm)


MODULES = ("base", "V", "P", "C")


@dataclass(frozen=True)
class Spot:
    """One placed piece. A part listed in more than one module gets a spot per module, keyed
    `id@module`; a part with a list of spots (three module sockets, say) shares its weight
    between them."""

    name: str
    part_id: str
    module: str | None  # None: wherever the build lists the part
    placement: Placement
    share: float


def parse_spots(place: dict) -> list[Spot]:
    spots = []
    for key, value in place.items():
        part_id, _, module = key.partition("@")
        if module and module not in MODULES:
            raise ValueError(f"{key}: {module} isn't a module (they're {', '.join(MODULES)})")
        listed = value if isinstance(value, list) else [value]
        placements = [
            v if isinstance(v, Placement) else Placement.model_validate(v) for v in listed
        ]
        for n, placement in enumerate(placements, start=1):
            name = key if len(placements) == 1 else f"{key} {n}"
            spots.append(Spot(name, part_id, module or None, placement, 1 / len(placements)))
    return spots


class Wire(Strict):
    name: str
    module: Literal["base", "V", "P", "C"] = "base"
    diameter_mm: float = Field(gt=0)
    path_mm: list[Point] = Field(min_length=2)

    @property
    def diameter(self) -> float:
        return units.mm_to_m(self.diameter_mm)

    @property
    def path(self) -> list[Point]:
        return [_m(p) for p in self.path_mm]


class Fastener(Strict):
    """A screw, nut or spacer, counted from the CAD's holes (see pcs14.cad.hardware)."""

    what: Literal["screw", "nut", "lock nut", "standoff", "spacer", "grommet", "patch"]
    count: int = Field(gt=0)
    holds: str  # the catalog part it fastens
    size: Literal["M2", "M2.5", "M3", "4-40"] | None = None
    length_mm: float | None = Field(default=None, gt=0)
    material: str | None = None  # a key in materials
    grams: float | None = Field(default=None, gt=0)  # each, for what has no standard shape
    module: Literal["base", "V", "P", "C"] | None = None  # when the part is in more than one
    note: str | None = None

    @model_validator(mode="after")
    def _weighable(self):
        if self.grams is not None:
            return self
        if self.size is None or self.material is None:
            raise ValueError(f"a {self.what} needs a size and a material, or its own grams")
        if self.what in ("screw", "standoff", "spacer") and self.length_mm is None:
            raise ValueError(f"a {self.what} needs a length_mm")
        if self.what in ("grommet", "patch"):
            raise ValueError(f"a {self.what} has no standard shape, so it needs grams")
        return self


class CadSettings(Strict):
    materials: dict[str, Material]
    print: Print
    checks: Checks
    pack: PackSettings
    legs: Legs
    rail: Rail
    gps_mast: GpsMast
    v_housing: VHousing
    p_holder: PHolder
    place: dict[str, Placement | list[Placement]]
    wires: list[Wire]
    hardware: list[Fastener] = Field(default_factory=list)

    @model_validator(mode="after")
    def _materials_exist(self):
        for item in self.hardware:
            if item.material is not None and item.material not in self.materials:
                raise ValueError(f"hardware for {item.holds}: no material {item.material}")
        return self

    def spots(self) -> list[Spot]:
        return parse_spots(self.place)

    def spot(self, name: str) -> Placement:
        """The placement of a part with a single spot, by its name."""
        for spot in self.spots():
            if spot.name == name:
                return spot.placement
        raise KeyError(f"nothing is placed as {name} in design/cad.yaml")


def load_settings(path: Path) -> CadSettings:
    path = Path(path)
    try:
        data = yaml.safe_load(path.read_text(encoding="utf-8"))
    except (OSError, yaml.YAMLError) as error:
        raise SettingsError(f"{path.name}: can't read it ({error})") from error
    try:
        return CadSettings.model_validate(data)
    except ValidationError as error:
        raise SettingsError(f"{path.name}: " + _explain(error)) from None
