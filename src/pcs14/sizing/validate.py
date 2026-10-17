"""The honesty check: run the model on published builds with measured flight times, and on
published cell discharge curves, and write down how far off it is.

A case file describes one published build: its motor, prop and pack (from the validation
catalog, kept apart from the real one so these parts never end up in the sweep), its
measured takeoff weight, estimates for what wasn't published (drag area, electronics), and
the measured flight time with the point it stopped at.
"""

import math
from dataclasses import dataclass
from pathlib import Path
from typing import Literal

import yaml
from pydantic import BaseModel, ConfigDict, Field, ValidationError, field_validator

from pcs14 import units
from pcs14.catalog import Catalog, CatalogError, Cell, Motor, Prop, Source
from pcs14.design import DesignError, PackSpec, _PackFile, pick_table
from pcs14.sizing.battery import Pack
from pcs14.sizing.flight import Flight, fly
from pcs14.sizing.rotor import DERATE, CannotHover, PowerModel, Rotor

STOPS = (
    "charge_used_fraction",
    "charge_used_mah",
    "loaded_voltage_per_cell_v",
    "resting_voltage_per_cell_v",
)


class Measured(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)

    kind: Literal["hover", "cruise"]
    speed_ms: float | None = Field(default=None, gt=0)
    minutes: float = Field(gt=0)
    until: dict[str, float]
    label: str  # independent measurement, builder's own measurement, manufacturer claim

    @field_validator("until")
    @classmethod
    def _one_stopping_point(cls, value: dict[str, float]) -> dict[str, float]:
        unknown = set(value) - set(STOPS)
        if unknown or len(value) != 1:
            raise ValueError(f"'until' needs exactly one of: {', '.join(STOPS)}")
        return value


class _CaseFile(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)

    name: str
    source: Source
    motor: str
    prop: str
    pack: _PackFile
    takeoff_weight_g: float = Field(gt=0)
    drag_area_cm2: float = Field(ge=0)
    avionics_power_w: float = Field(ge=0)
    estimate_note: str = Field(min_length=1)  # how drag and electronics were estimated
    measured: Measured


class ValidationCase(BaseModel):
    model_config = ConfigDict(frozen=True, arbitrary_types_allowed=True)

    name: str
    source: Source
    motor: Motor
    prop: Prop
    pack: PackSpec
    takeoff_weight_g: float
    drag_area_cm2: float
    avionics_power_w: float
    estimate_note: str
    measured: Measured

    @property
    def weight(self) -> float:
        return units.g_to_kg(self.takeoff_weight_g) * units.G0


def load_cases(folder: Path, catalog: Catalog) -> list[ValidationCase]:
    cases = []
    for path in sorted(Path(folder).glob("*.yaml")):
        try:
            raw = _CaseFile.model_validate(yaml.safe_load(path.read_text(encoding="utf-8")))
        except ValidationError as error:
            raise DesignError(f"{path.name}: {error}") from None
        try:
            cases.append(
                ValidationCase(
                    name=raw.name,
                    source=raw.source,
                    motor=catalog.motor(raw.motor),
                    prop=catalog.prop(raw.prop),
                    pack=PackSpec(
                        cell=catalog.cell(raw.pack.cell),
                        series=raw.pack.series,
                        parallel=raw.pack.parallel,
                        overhead=units.g_to_kg(raw.pack.overhead_g),
                        wiring_resistance=units.mohm_to_ohm(raw.pack.wiring_mohm),
                    ),
                    takeoff_weight_g=raw.takeoff_weight_g,
                    drag_area_cm2=raw.drag_area_cm2,
                    avionics_power_w=raw.avionics_power_w,
                    estimate_note=raw.estimate_note,
                    measured=raw.measured,
                )
            )
        except CatalogError as error:
            raise CatalogError(f"{path.name}: {error}") from None
    return cases


@dataclass(frozen=True)
class Comparison:
    case: ValidationCase
    flight: Flight | None  # the model's flight on the published numbers
    predicted_minutes: float
    predicted_pessimistic: float
    note: str = ""

    @property
    def measured_minutes(self) -> float:
        return self.case.measured.minutes

    @property
    def error(self) -> float:
        """How far off the model is, as a fraction: +0.10 means 10% too long."""
        return (self.predicted_minutes - self.measured_minutes) / self.measured_minutes

    @property
    def inside_the_band(self) -> bool:
        """Whether the measurement lands between the pessimistic and published predictions."""
        return self.predicted_pessimistic <= self.measured_minutes <= self.predicted_minutes


def compare_case(case: ValidationCase, dt: float = 1.0) -> Comparison:
    pack = Pack(case.pack)
    table = pick_table(case.motor, case.prop, case.pack.series * 3.6)
    speed = 0.0 if case.measured.kind == "hover" else (case.measured.speed_ms or 0.0)
    ((stop_kind, stop_value),) = case.measured.until.items()
    reserve, stop = 0.0, None
    if stop_kind == "charge_used_fraction":
        reserve = 1 - stop_value
    elif stop_kind == "charge_used_mah":
        reserve = 1 - stop_value / pack.capacity_mah
    elif stop_kind == "loaded_voltage_per_cell_v":

        def stop(sample):
            return sample.voltage <= stop_value * case.pack.series
    else:

        def stop(sample):
            return pack.ocv(sample.soc) <= stop_value * case.pack.series

    flights = {}
    for name, scale in (("nominal", 1.0), ("pessimistic", 1 - DERATE[table.source.kind])):
        try:
            model = PowerModel(
                rotor=Rotor(table=table, prop=case.prop, thrust_scale=scale),
                weight=case.weight,
                drag_area=units.cm2_to_m2(case.drag_area_cm2),
                avionics_power=case.avionics_power_w,
            )
        except CannotHover as error:
            return Comparison(case, None, 0.0, 0.0, note=str(error))
        flights[name] = fly(model, pack, speed, reserve, dt=dt, stop=stop)
    return Comparison(
        case=case,
        flight=flights["nominal"],
        predicted_minutes=flights["nominal"].minutes,
        predicted_pessimistic=flights["pessimistic"].minutes,
    )


@dataclass(frozen=True)
class DischargeCheck:
    cell: Cell
    current: float
    source: Source
    points: tuple[tuple[float, float, float], ...]  # (mAh delivered, measured V, model V)

    @property
    def errors(self) -> list[float]:
        return [measured - model for _, measured, model in self.points]

    @property
    def rms_error(self) -> float:
        return math.sqrt(sum(e * e for e in self.errors) / len(self.errors))

    @property
    def mean_error(self) -> float:
        """Negative means the real cell sags more than the model says."""
        return sum(self.errors) / len(self.errors)


def discharge_check(cell: Cell) -> list[DischargeCheck]:
    """The model's voltage at each point of every published discharge test for this cell."""
    single = Pack(PackSpec(cell=cell, series=1, parallel=1, overhead=0.0, wiring_resistance=0.0))
    checks = []
    for test in cell.discharge_tests:
        points = []
        for point in test.points:
            soc = 1 - point.capacity_mah / cell.capacity_mah
            model = single.terminal_voltage(soc, test.current_a)
            points.append((point.capacity_mah, point.voltage_v, model))
        checks.append(DischargeCheck(cell, test.current_a, test.source, tuple(points)))
    return checks
