"""A part's cad block: its shape, where the dimensions came from, which ones are estimates,
and whether a CAD model of it already exists (checked before modeling, even when the answer
is "none found").

Dimensions carry _mm in their names, like every unit in the catalog; `size()` and the hole
properties hand them back in meters. Each shape is one builder in pcs14.cad. Two shapes have
no dimensions here: "printed" parts are designed in code, and "routed" parts (the wiring) come
from the wire routes in design/cad.yaml.
"""

from datetime import date
from typing import Annotated, Literal

from pydantic import Field, HttpUrl, model_validator

from pcs14 import units
from pcs14.catalog.source import Source, Strict

MM = Field(gt=0)


class ExistingCad(Strict):
    found: Literal["official", "unofficial", "none"]
    url: HttpUrl | None = None
    download_url: HttpUrl | None = None  # the file itself, for the local cache, when there's one
    format: str | None = None
    terms: str | None = None  # what the license or terms say, or that they say nothing
    checked: date
    note: str | None = None

    @model_validator(mode="after")
    def _found_ones_say_where(self):
        if self.found != "none" and (self.url is None or not self.terms):
            raise ValueError(
                "a CAD model that was found needs its link and its terms (url and terms), "
                "so it's clear whether it can be used"
            )
        return self


class Hole(Strict):
    x_mm: float  # from the part's center
    y_mm: float
    diameter_mm: float = MM

    @property
    def x(self) -> float:
        return units.mm_to_m(self.x_mm)

    @property
    def y(self) -> float:
        return units.mm_to_m(self.y_mm)

    @property
    def diameter(self) -> float:
        return units.mm_to_m(self.diameter_mm)


class CadConnector(Strict):
    """Where one of the part's connectors sits, pin by pin, in the part's own frame (mm from
    its middle, the way pcs14.cad.parts builds it), so every wire can be drawn pin to pin. The
    names are its electrical block's. A part placed more than once (one fuse per branch) says
    which placement holds it."""

    name: str
    side: Literal["top", "bottom", "edge"]
    faces: Literal["+x", "-x", "+y", "-y", "up", "down"] | None = None  # the way its plug comes in
    z_mm: float | None = None  # its height, for an edge connector or to say it outright
    instance: int = Field(default=0, ge=0)  # which of the part's placements in design/cad.yaml
    pins: dict[str, tuple[float, float]] = Field(min_length=1)  # each pin's x_mm, y_mm
    source: Source  # an estimate's note says how it was worked out

    @model_validator(mode="after")
    def _edges_say_how_high(self):
        if self.side == "edge" and self.z_mm is None:
            raise ValueError(f"connector {self.name} is on an edge, so it needs its z_mm")
        return self

    def z(self, thickness_mm: float) -> float:
        """Its height in mm: on top of a part `thickness_mm` thick, under it, or as given."""
        if self.z_mm is not None:
            return self.z_mm
        return thickness_mm if self.side == "top" else 0.0


class CadBlock(Strict):
    source: Source
    estimates: list[str] = Field(default_factory=list)  # names of dimensions that are estimates
    estimate_note: str | None = None
    existing: ExistingCad
    connectors: list[CadConnector] = Field(default_factory=list)

    @model_validator(mode="after")
    def _estimates_are_real_and_explained(self):
        dimensions = {name for name in type(self).model_fields if name.endswith("_mm")}
        unknown = [name for name in self.estimates if name not in dimensions]
        if unknown:
            known = ", ".join(sorted(dimensions)) or "none"
            raise ValueError(
                f"estimates names {', '.join(unknown)}, which isn't a dimension of a "
                f"{self.shape} (they're: {known})"
            )
        if self.estimates and not self.estimate_note:
            raise ValueError("estimates need an estimate_note saying how they were worked out")
        return self

    def size(self, name: str) -> float:
        """A dimension in meters."""
        return units.mm_to_m(getattr(self, name))


class BoxCad(CadBlock):
    shape: Literal["box"]
    length_mm: float = MM
    width_mm: float = MM
    height_mm: float = MM


class CylinderCad(CadBlock):
    shape: Literal["cylinder"]
    diameter_mm: float = MM
    length_mm: float = MM


class BoardCad(CadBlock):
    shape: Literal["board"]
    length_mm: float = MM
    width_mm: float = MM
    thickness_mm: float = MM
    top_mm: float = Field(ge=0)  # tallest part above the board
    bottom_mm: float = Field(default=0, ge=0)  # tallest part below it
    holes: list[Hole] = Field(default_factory=list)


class MotorCad(CadBlock):
    shape: Literal["motor"]
    diameter_mm: float = MM
    length_mm: float = MM  # base, bell and shaft together
    bell_length_mm: float = MM
    shaft_diameter_mm: float = MM
    mount_spacing_mm: float = MM  # square pattern, hole to hole
    mount_hole_mm: float = MM


class PropCad(CadBlock):
    shape: Literal["prop"]
    hub_diameter_mm: float = MM
    hub_thickness_mm: float = MM
    bore_mm: float = MM
    blade_width_mm: float = MM


class CellCad(CadBlock):
    shape: Literal["cell"]
    diameter_mm: float = MM
    length_mm: float = MM


class FrameCad(CadBlock):
    """A plain X: a bottom plate, the arms on it, a middle plate on the arms, the stack bay,
    then the top plate. The motors sit on the arms at the wheelbase's corners."""

    shape: Literal["frame"]
    arm_thickness_mm: float = MM
    arm_width_mm: float = MM
    motor_pad_mm: float = MM  # the round pad at the end of each arm
    plate_thickness_mm: float = MM
    plate_gap_mm: float = MM  # the stack bay, between the middle and top plates
    body_front_mm: float = MM  # how far the body plates reach ahead of the motors' center
    body_back_mm: float = MM  # and behind it
    body_width_mm: float = MM
    nose_from_mm: float  # where the plates narrow, ahead of the motors' center
    nose_width_mm: float = MM
    stack_spacing_mm: float = MM  # the flight controller stack's hole pattern
    max_stack_mm: float = MM


class PrintedCad(CadBlock):
    shape: Literal["printed"]  # designed in pcs14.cad.printed


class RoutedCad(CadBlock):
    shape: Literal["routed"]  # modeled by the wire routes in design/cad.yaml


class FastenersCad(CadBlock):
    shape: Literal["fasteners"]  # design/cad.yaml's hardware list, on the parts it holds


AnyCad = Annotated[
    BoxCad
    | CylinderCad
    | BoardCad
    | MotorCad
    | PropCad
    | CellCad
    | FrameCad
    | PrintedCad
    | RoutedCad
    | FastenersCad,
    Field(discriminator="shape"),
]
