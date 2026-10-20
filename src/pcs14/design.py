"""The targets (design/targets.yaml) and a build (which part fills each slot), as objects."""

import dataclasses
from dataclasses import dataclass
from itertools import combinations as choose
from pathlib import Path
from typing import Literal

import yaml
from pydantic import BaseModel, ConfigDict, Field, ValidationError

from pcs14 import units
from pcs14.catalog import Catalog, CatalogError, Cell, Component, Esc, Frame, Motor, Prop
from pcs14.catalog.schema import SourceKind, ThrustTable

MODULES = ("V", "P", "C")
NOMINAL_CELL_VOLTAGE = 3.6  # used only to pick the thrust table closest to the pack's voltage


class DesignError(Exception):
    """The targets or a build file is broken, or the parts in a build don't fit together."""


# --- targets ---------------------------------------------------------------------------


class _Strict(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)


class _SetupFile(_Strict):
    modules: list[Literal["V", "P", "C"]]
    required: bool = True
    min_cruise_time_min: float = Field(gt=0)
    min_hover_time_min: float = Field(gt=0)
    payload_g: float = Field(default=0, ge=0)
    min_top_speed_kmh: float | None = Field(default=None, gt=0)
    hold_position_in_wind_ms: float | None = Field(default=None, gt=0)
    max_takeoff_weight_g: float | None = Field(default=None, gt=0)


class _EverySetupFile(_Strict):
    min_thrust_to_weight: float = Field(gt=1)
    current_within_battery_rating: bool


class _HoverPass(_Strict):
    duration_s: float = Field(gt=0)
    max_drift_m: float = Field(gt=0)  # sideways, in still air
    max_height_error_m: float = Field(gt=0)


class _StepsPass(_Strict):
    max_settle_s: float = Field(gt=0)
    max_overshoot: float = Field(ge=0)  # a share of the step


class _WindPass(_Strict):
    max_drift_m: float = Field(gt=0)  # the wind's speed is each setup's hold_position_in_wind_ms
    max_motor_share: float = Field(gt=0, le=1)  # of each motor's top speed


class _EndurancePass(_Strict):
    max_difference: float = Field(gt=0, lt=1)  # a share of the sizing model's times


class _PayloadPass(_Strict):
    max_drift_m: float = Field(gt=0)


class _ReturnsPass(_Strict):
    max_landing_distance_m: float = Field(gt=0)  # from where it took off


class _FailuresPass(_Strict):
    max_touchdown_ms: float = Field(gt=0)  # the descent rate just before a controlled touchdown
    max_distance_m: float = Field(gt=0)  # from where the failure hit; farther is a fly-away


class TriggerThresholds(_Strict):
    """The safety monitor's automatic triggers, in shadow mode until they show no false
    triggers (docs/specs/2026-10-19-flight-sim.md)."""

    free_fall_g: float = Field(gt=0, lt=1)  # total acceleration under this, in g
    free_fall_s: float = Field(gt=0)
    tumble_rate_dps: float = Field(gt=0)  # body rate over this, in degrees a second
    tumble_rate_s: float = Field(gt=0)
    tumble_tilt_deg: float = Field(gt=0, lt=180)
    tumble_tilt_s: float = Field(gt=0)


class FlightSimTargets(_Strict):
    """What passing means in the flight sim (step 4). Top speed, the wind's speed, the reserve and
    the payload come from the setups and the rest of the targets."""

    hover: _HoverPass
    steps: _StepsPass
    wind: _WindPass
    endurance: _EndurancePass
    payload: _PayloadPass
    returns: _ReturnsPass
    failures: _FailuresPass
    triggers: TriggerThresholds
    max_false_triggers: int = Field(ge=0)


class _TargetsFile(_Strict):
    reserve_battery_fraction: float = Field(gt=0, lt=1)
    cruise_speed_ms: float = Field(gt=0)
    sizing_case: str
    growth_margin_g: float = Field(ge=0)
    every_setup: _EverySetupFile
    setups: dict[str, _SetupFile]
    flight_sim: FlightSimTargets | None = None


@dataclass(frozen=True)
class SetupTargets:
    """What one module combination has to hit, in metric."""

    name: str
    modules: frozenset[str]
    required: bool
    min_cruise_time: float  # s
    min_hover_time: float  # s
    payload: float  # kg
    min_top_speed: float | None  # m/s
    hold_position_in_wind: float | None  # m/s
    max_takeoff_weight: float | None  # kg


@dataclass(frozen=True)
class Targets:
    reserve_fraction: float
    cruise_speed: float  # m/s
    sizing_case: str
    growth_margin: float  # kg
    min_thrust_to_weight: float
    current_within_battery_rating: bool
    setups: dict[str, SetupTargets]
    flight_sim: FlightSimTargets | None = None

    def combinations(self) -> list[SetupTargets]:
        """All eight module combinations. The named setups keep their own targets; the others
        borrow from the smallest named setup that holds all their modules."""
        named = {setup.modules: setup for setup in self.setups.values()}
        result = []
        for count in range(len(MODULES) + 1):
            for chosen in choose(MODULES, count):
                modules = frozenset(chosen)
                if modules in named:
                    result.append(named[modules])
                    continue
                holders = [s for s in self.setups.values() if modules <= s.modules]
                if not holders:
                    raise DesignError(f"no setup in the targets holds modules {'+'.join(chosen)}")
                donor = min(holders, key=lambda s: len(s.modules))
                result.append(
                    dataclasses.replace(
                        donor,
                        name="+".join(chosen),
                        modules=modules,
                        payload=donor.payload if "C" in modules else 0.0,
                    )
                )
        return result


def load_targets(path: Path) -> Targets:
    path = Path(path)
    data = _read_yaml(path)
    try:
        raw = _TargetsFile.model_validate(data)
    except ValidationError as error:
        raise DesignError(f"{path.name}: " + _explain(error)) from None

    setups = {
        name: SetupTargets(
            name=name,
            modules=frozenset(s.modules),
            required=s.required,
            min_cruise_time=units.minutes_to_seconds(s.min_cruise_time_min),
            min_hover_time=units.minutes_to_seconds(s.min_hover_time_min),
            payload=units.g_to_kg(s.payload_g),
            min_top_speed=None
            if s.min_top_speed_kmh is None
            else units.kmh_to_ms(s.min_top_speed_kmh),
            hold_position_in_wind=s.hold_position_in_wind_ms,
            max_takeoff_weight=(
                None if s.max_takeoff_weight_g is None else units.g_to_kg(s.max_takeoff_weight_g)
            ),
        )
        for name, s in raw.setups.items()
    }
    if raw.sizing_case not in setups:
        raise DesignError(f"{path.name}: sizing_case '{raw.sizing_case}' isn't one of the setups")
    if not setups[raw.sizing_case].required:
        raise DesignError(
            f"{path.name}: sizing_case '{raw.sizing_case}' has to be a required setup, since it's "
            "the one the motors get sized for"
        )
    return Targets(
        reserve_fraction=raw.reserve_battery_fraction,
        cruise_speed=raw.cruise_speed_ms,
        sizing_case=raw.sizing_case,
        growth_margin=units.g_to_kg(raw.growth_margin_g),
        min_thrust_to_weight=raw.every_setup.min_thrust_to_weight,
        current_within_battery_rating=raw.every_setup.current_within_battery_rating,
        setups=setups,
        flight_sim=raw.flight_sim,
    )


# --- builds ----------------------------------------------------------------------------


class _PackFile(_Strict):
    cell: str
    series: int = Field(ge=1)
    parallel: int = Field(ge=1)
    overhead_g: float = Field(ge=0)
    wiring_mohm: float = Field(ge=0)
    note: str = Field(min_length=1)  # these two numbers are estimates until the electrical step


class _FirmwareFile(_Strict):
    # The flight controller caps total battery current at this share of the pack's
    # continuous rating. Leave it out for no cap.
    current_cap_fraction: float | None = Field(default=None, gt=0)


class _BuildFile(_Strict):
    motor: str
    prop: str
    esc: str
    frame: str
    pack: _PackFile
    base: list[str]
    modules: dict[Literal["V", "P", "C"], list[str]]
    firmware: _FirmwareFile = Field(default_factory=_FirmwareFile)


@dataclass(frozen=True)
class PackSpec:
    cell: Cell
    series: int
    parallel: int
    overhead: float  # kg: nickel strip, wires, wrap
    wiring_resistance: float  # ohms, battery to ESC

    @property
    def cell_count(self) -> int:
        return self.series * self.parallel

    @property
    def mass(self) -> float:
        return self.cell_count * self.cell.mass + self.overhead

    @property
    def label(self) -> str:
        return f"{self.series}S{self.parallel}P {self.cell.maker} {self.cell.model}"


@dataclass(frozen=True)
class Build:
    motor: Motor
    prop: Prop
    esc: Esc
    frame: Frame
    pack: PackSpec
    base: tuple[Component, ...]
    modules: dict[str, tuple[Component, ...]]
    current_cap_fraction: float | None = None  # of the pack's continuous rating, in firmware

    def __post_init__(self):
        _check_fit(self)

    @property
    def current_cap(self) -> float | None:
        """A: the most current the firmware lets all four motors pull from the pack."""
        if self.current_cap_fraction is None:
            return None
        rating = self.pack.parallel * self.pack.cell.max_continuous_a  # as in Pack
        return rating * self.current_cap_fraction

    @property
    def thrust_table(self) -> ThrustTable:
        return pick_table(self.motor, self.prop, self.pack.series * NOMINAL_CELL_VOLTAGE)

    def all_module_parts(self) -> tuple[Component, ...]:
        return tuple(p for parts in self.modules.values() for p in parts)

    def carried(self, modules: frozenset[str]) -> tuple[Component, ...]:
        """The base parts, plus the parts of every module fitted."""
        parts = list(self.base)
        for module in MODULES:
            if module in modules:
                parts += self.modules.get(module, ())
        return tuple(parts)

    def variant(self, **changes) -> "Build":
        """The same build with some parts swapped (motor, prop, cell or parallel), or a
        different current cap."""
        pack_changes = {k: changes.pop(k) for k in ("cell", "series", "parallel") if k in changes}
        pack = dataclasses.replace(self.pack, **pack_changes)
        return dataclasses.replace(self, pack=pack, **changes)

    @property
    def label(self) -> str:
        return f"{self.motor.model} / {self.prop.model} / {self.pack.label}"


# Measured beats published, and anything beats a guess.
SOURCE_RANK = {
    SourceKind.THRUST_STAND: 0,
    SourceKind.INDEPENDENT_TEST: 1,
    SourceKind.MANUFACTURER: 2,
    SourceKind.ESTIMATE: 3,
    SourceKind.MADE_UP: 4,
}


def pick_table(motor: Motor, prop: Prop, pack_voltage: float) -> ThrustTable:
    """The best thrust table for this motor and prop: the best source wins, and the voltage
    closest to the pack's breaks a tie."""
    tables = motor.tables_for(prop.id)
    if not tables:
        raise DesignError(f"the motor {motor.id} has no thrust table for the prop {prop.id}")
    return min(tables, key=lambda t: (SOURCE_RANK[t.source.kind], abs(t.voltage - pack_voltage)))


def load_build(path: Path, catalog: Catalog) -> Build:
    path = Path(path)
    data = _read_yaml(path)
    try:
        raw = _BuildFile.model_validate(data)
    except ValidationError as error:
        raise DesignError(f"{path.name}: " + _explain(error)) from None
    try:
        return Build(
            motor=catalog.motor(raw.motor),
            prop=catalog.prop(raw.prop),
            esc=catalog.esc(raw.esc),
            frame=catalog.frame(raw.frame),
            pack=PackSpec(
                cell=catalog.cell(raw.pack.cell),
                series=raw.pack.series,
                parallel=raw.pack.parallel,
                overhead=units.g_to_kg(raw.pack.overhead_g),
                wiring_resistance=units.mohm_to_ohm(raw.pack.wiring_mohm),
            ),
            base=tuple(catalog.component(c) for c in raw.base),
            modules={m: tuple(catalog.component(c) for c in ids) for m, ids in raw.modules.items()},
            current_cap_fraction=raw.firmware.current_cap_fraction,
        )
    except CatalogError as error:
        raise CatalogError(f"{path.name}: {error}") from None
    except DesignError as error:
        raise DesignError(f"{path.name}: {error}") from None


def _check_fit(build: Build) -> None:
    if not build.motor.tables_for(build.prop.id):
        tested = ", ".join(sorted({t.prop for t in build.motor.thrust_tables}))
        raise DesignError(
            f"the motor {build.motor.id} has no thrust table for the prop {build.prop.id} "
            f"(it has tables for: {tested})"
        )
    if build.prop.diameter_in > build.frame.max_prop_in:
        raise DesignError(
            f'the {build.prop.diameter_in}" prop is too big for the {build.frame.id} frame '
            f'(it takes up to {build.frame.max_prop_in}")'
        )
    series = build.pack.series
    for part in (build.motor, build.esc):
        if not part.cells_min <= series <= part.cells_max:
            raise DesignError(
                f"a {series}S pack is outside what {part.id} takes "
                f"({part.cells_min}S to {part.cells_max}S)"
            )
    for module in build.modules:
        if module not in MODULES:
            raise DesignError(f"'{module}' isn't a module (they're {', '.join(MODULES)})")


def _read_yaml(path: Path) -> dict:
    if not path.is_file():
        raise DesignError(f"there's no file at {path}")
    try:
        data = yaml.safe_load(path.read_text(encoding="utf-8"))
    except yaml.YAMLError as error:
        raise DesignError(f"{path.name}: isn't valid YAML ({error})") from error
    if not isinstance(data, dict):
        raise DesignError(f"{path.name}: should be a set of fields")
    return data


def _explain(error: ValidationError) -> str:
    parts = []
    for problem in error.errors():
        where = ".".join(str(step) for step in problem["loc"]) or "the file"
        message = problem["msg"].removeprefix("Value error, ")
        if problem["type"] == "literal_error":
            message += f" (got {problem['input']!r})"
        parts.append(f"{where}: {message}")
    return "; ".join(parts)
