"""What each parts file has to look like.

Numbers in the files carry their unit in the field name (mass_g, diameter_in, capacity_mah),
and the properties on each part hand them back in meters, kilograms, seconds, newtons,
watts, volts, amps and coulombs. Every number has a source: the part's own `source` covers
its specs, and thrust tables, voltage curves, resistances, power draws and drag areas each
carry their own.
"""

import math
from datetime import date
from typing import Any, Literal

from pydantic import Field, HttpUrl, model_validator

from pcs14 import units
from pcs14.catalog.cad import AnyCad
from pcs14.catalog.electrical import ElectricalBlock
from pcs14.catalog.source import Source, SourceKind, Strict

__all__ = ["Source", "SourceKind", "Strict"]

ID_PATTERN = r"^[a-z0-9][a-z0-9.-]*$"


class Part(Strict):
    type: str
    id: str = Field(pattern=ID_PATTERN)
    maker: str
    model: str
    part_number: str | None = None
    link: HttpUrl | None = None
    price_usd: float | None = Field(default=None, ge=0)
    checked: date | None = None
    source: Source
    mass_g: float = Field(gt=0)
    cad: AnyCad | None = None  # every part in the build gets one; see pcs14.catalog.cad
    electrical: ElectricalBlock | None = None  # see pcs14.catalog.electrical

    @property
    def mass(self) -> float:
        return units.g_to_kg(self.mass_g)

    def sources(self) -> list[Source]:
        blocks = [b for b in (self.cad, self.electrical) if b is not None]
        return [self.source] + [b.source for b in blocks]


class ThrustRow(Strict):
    throttle_pct: float = Field(gt=0, le=100)
    thrust_g: float = Field(gt=0)
    current_a: float = Field(gt=0)
    rpm: float | None = Field(default=None, gt=0)
    power_w: float | None = Field(default=None, gt=0)  # filled in as volts x amps if missing

    @property
    def thrust(self) -> float:
        return units.gram_force_to_newton(self.thrust_g)

    @property
    def power(self) -> float:
        assert self.power_w is not None
        return self.power_w


class ThrustTable(Strict):
    prop: str
    voltage_v: float = Field(gt=0)
    source: Source
    rows: list[ThrustRow] = Field(min_length=3)

    @model_validator(mode="before")
    @classmethod
    def _fill_in_power(cls, data: Any) -> Any:
        if isinstance(data, dict) and isinstance(data.get("rows"), list):
            volts = data.get("voltage_v")
            for row in data["rows"]:
                if isinstance(row, dict) and "power_w" not in row and volts and "current_a" in row:
                    row["power_w"] = volts * row["current_a"]
        return data

    @model_validator(mode="after")
    def _rises_with_throttle(self):
        if self.source.kind is SourceKind.CAD:
            raise ValueError("a thrust table can't come from the CAD, only from a test")
        for before, after in zip(self.rows, self.rows[1:], strict=False):
            if after.throttle_pct <= before.throttle_pct:
                raise ValueError("rows have to go in order of rising throttle")
            if after.thrust_g <= before.thrust_g:
                raise ValueError(f"thrust has to rise with throttle (at {after.throttle_pct}%)")
            if after.current_a <= before.current_a:
                raise ValueError(f"current has to rise with throttle (at {after.throttle_pct}%)")
        return self

    @property
    def voltage(self) -> float:
        return self.voltage_v


class Motor(Part):
    type: Literal["motor"]
    kv: float = Field(gt=0)
    cells_min: int = Field(ge=1)
    cells_max: int = Field(ge=1)
    max_current_a: float = Field(gt=0)
    thrust_tables: list[ThrustTable] = Field(min_length=1)

    @model_validator(mode="after")
    def _cell_range(self):
        if self.cells_min > self.cells_max:
            raise ValueError("cells_min can't be more than cells_max")
        return self

    def sources(self) -> list[Source]:
        return [*super().sources(), *(table.source for table in self.thrust_tables)]

    def tables_for(self, prop_id: str) -> list[ThrustTable]:
        return [table for table in self.thrust_tables if table.prop == prop_id]


class Prop(Part):
    type: Literal["prop"]
    diameter_in: float = Field(gt=0)
    pitch_in: float = Field(gt=0)
    blades: int = Field(ge=2)

    @property
    def diameter(self) -> float:
        return units.inch_to_m(self.diameter_in)

    @property
    def radius(self) -> float:
        return self.diameter / 2

    @property
    def disk_area(self) -> float:
        return math.pi * self.radius**2

    @property
    def pitch(self) -> float:
        return units.inch_to_m(self.pitch_in)


class OcvPoint(Strict):
    soc: float = Field(ge=0, le=1)
    voltage_v: float = Field(gt=0)


class DischargePoint(Strict):
    capacity_mah: float = Field(ge=0)  # delivered so far
    voltage_v: float = Field(gt=0)  # under load


class DischargeTest(Strict):
    """A measured discharge at a steady current, for checking the battery model against."""

    current_a: float = Field(gt=0)
    source: Source
    points: list[DischargePoint] = Field(min_length=2)

    @model_validator(mode="after")
    def _runs_downhill(self):
        for before, after in zip(self.points, self.points[1:], strict=False):
            if after.capacity_mah <= before.capacity_mah:
                raise ValueError("discharge points have to go in order of rising capacity")
            if after.voltage_v > before.voltage_v:
                raise ValueError("voltage can't rise during a steady discharge")
        return self


class Cell(Part):
    type: Literal["cell"]
    capacity_mah: float = Field(gt=0)
    max_continuous_a: float = Field(gt=0)
    min_voltage_v: float = Field(gt=0)
    max_voltage_v: float = Field(gt=0)
    internal_resistance_mohm: float = Field(gt=0)
    resistance_source: Source
    ocv_source: Source
    ocv_curve: list[OcvPoint] = Field(min_length=3)
    discharge_tests: list[DischargeTest] = Field(default_factory=list)

    @model_validator(mode="after")
    def _curve_runs_empty_to_full(self):
        curve = self.ocv_curve
        if curve[0].soc != 0:
            raise ValueError("the voltage curve has to start at empty (soc 0)")
        if curve[-1].soc != 1:
            raise ValueError("the voltage curve has to end at full (soc 1)")
        for before, after in zip(curve, curve[1:], strict=False):
            if after.soc <= before.soc:
                raise ValueError("the voltage curve has to go in order of rising charge")
            if after.voltage_v < before.voltage_v:
                raise ValueError("voltage can't drop as the charge rises")
        if self.min_voltage_v >= self.max_voltage_v:
            raise ValueError("min_voltage_v has to be below max_voltage_v")
        if curve[-1].voltage_v > self.max_voltage_v:
            raise ValueError("the voltage curve goes above max_voltage_v")
        return self

    def sources(self) -> list[Source]:
        return [
            *super().sources(),
            self.resistance_source,
            self.ocv_source,
            *(test.source for test in self.discharge_tests),
        ]

    @property
    def capacity(self) -> float:
        return units.mah_to_coulomb(self.capacity_mah)

    @property
    def internal_resistance(self) -> float:
        return units.mohm_to_ohm(self.internal_resistance_mohm)


class Esc(Part):
    type: Literal["esc"]
    cells_min: int = Field(ge=1)
    cells_max: int = Field(ge=1)
    continuous_a_per_motor: float = Field(gt=0)
    burst_a_per_motor: float = Field(gt=0)
    bidirectional_dshot: bool

    @model_validator(mode="after")
    def _ratings(self):
        if self.cells_min > self.cells_max:
            raise ValueError("cells_min can't be more than cells_max")
        if self.burst_a_per_motor < self.continuous_a_per_motor:
            raise ValueError("burst_a_per_motor can't be below continuous_a_per_motor")
        return self


class Frame(Part):
    type: Literal["frame"]
    max_prop_in: float = Field(gt=0)
    wheelbase_mm: float = Field(gt=0)
    drag_area_cm2: float = Field(ge=0)
    drag_source: Source

    def sources(self) -> list[Source]:
        return [*super().sources(), self.drag_source]

    @property
    def drag_area(self) -> float:
        """Drag coefficient times frontal area, in square meters."""
        return units.cm2_to_m2(self.drag_area_cm2)

    @property
    def wheelbase(self) -> float:
        return units.mm_to_m(self.wheelbase_mm)


class Component(Part):
    """Anything else with a mass: flight controller, receiver, module parts, wiring."""

    type: Literal["component"]
    power_w: float = Field(default=0, ge=0)
    power_source: Source | None = None
    drag_area_cm2: float = Field(default=0, ge=0)
    drag_source: Source | None = None

    @model_validator(mode="after")
    def _sourced(self):
        if self.power_w > 0 and self.power_source is None:
            raise ValueError("power_w needs a power_source saying where the number came from")
        if self.drag_area_cm2 > 0 and self.drag_source is None:
            raise ValueError("drag_area_cm2 needs a drag_source saying where the number came from")
        return self

    def sources(self) -> list[Source]:
        extra = [s for s in (self.power_source, self.drag_source) if s is not None]
        return [*super().sources(), *extra]

    @property
    def power(self) -> float:
        return self.power_w

    @property
    def drag_area(self) -> float:
        return units.cm2_to_m2(self.drag_area_cm2)


class WireGauge(Strict):
    awg: int
    resistance_mohm_per_m: float = Field(gt=0)  # the conductor, at 20 °C
    outer_diameter_mm: float = Field(gt=0)  # over the insulation
    mass_g_per_m: float = Field(gt=0)

    @property
    def resistance_per_m(self) -> float:
        return units.mohm_to_ohm(self.resistance_mohm_per_m)

    @property
    def outer_diameter(self) -> float:
        return units.mm_to_m(self.outer_diameter_mm)

    @property
    def mass_per_m(self) -> float:
        return units.g_to_kg(self.mass_g_per_m)


class Wire(Part):
    """A kind of hookup wire, as a table of gauges. It has no mass of its own: each gauge has
    grams per meter, and the connection list says how much of each the drone carries."""

    type: Literal["wire"]
    mass_g: None = None
    insulation_max_c: float | None  # None for bare wire
    gauges: list[WireGauge] = Field(min_length=1)

    @model_validator(mode="after")
    def _thicker_conducts_better(self):
        by_size = sorted(self.gauges, key=lambda g: g.awg)
        if len({g.awg for g in by_size}) != len(by_size):
            raise ValueError("a gauge is listed twice")
        for thick, thin in zip(by_size, by_size[1:], strict=False):
            if thick.resistance_mohm_per_m >= thin.resistance_mohm_per_m:
                raise ValueError(
                    f"{thick.awg} AWG has more resistance than {thin.awg} AWG, which is thinner"
                )
        return self

    @property
    def mass(self) -> float:
        raise AttributeError("a wire table has no single mass: each gauge has its mass per meter")

    def gauge(self, awg: int) -> WireGauge:
        for gauge in self.gauges:
            if gauge.awg == awg:
                return gauge
        listed = ", ".join(str(g.awg) for g in sorted(self.gauges, key=lambda g: g.awg))
        raise KeyError(f"there's no {awg} AWG in this wire table (it has {listed})")
