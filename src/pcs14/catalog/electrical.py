"""A part's electrical block: its connectors and pins, the current it draws, the supplies it
provides, and its ratings if it's a connector or a fuse. Every block has a source, and names
the numbers that are estimates.

Pins are named CONNECTOR.PIN everywhere (the flight controller's "CAN.5V"), so the connection
list in design/electrical.yaml can point at them. A connector's `family` is the catalog id of
the part that holds its contact rating (a JST-GH, an XT60), or "pads" for solder pads and
header pins, which have no published rating.

Estimates are named like `draws[ESC.VBAT].worst_a`, `outputs[5V]` or `connectors[ESC]` (the
whole pinout), so a check that rests on one can say so.
"""

import math
import re
from collections.abc import Iterator
from typing import Literal

from pydantic import Field, field_validator, model_validator

from pcs14 import units
from pcs14.catalog.source import Source, Strict

NAME = r"^[A-Za-z0-9_+-]+$"  # no dots: a dot separates the connector from the pin
PADS = "pads"


class Pin(Strict):
    name: str = Field(pattern=NAME)
    role: Literal["power", "ground", "signal", "bus"]  # bus: a differential pair, like CAN
    direction: Literal["in", "out", "both"] | None = None  # signals only
    volts: float | None = Field(default=None, gt=0)  # power: nominal; signal: logic high
    max_volts: float | None = Field(default=None, gt=0)  # the most it takes
    functions: list[str] = Field(default_factory=list)  # what else it can be: UART2_RX, PWM

    @model_validator(mode="after")
    def _signals_say_which_way_and_how_high(self):
        if self.role == "signal" and (self.direction is None or self.volts is None):
            raise ValueError(
                f"signal pin {self.name} needs a direction and volts (its logic level)"
            )
        return self


class Connector(Strict):
    name: str = Field(pattern=NAME)
    family: str  # the catalog part holding its contact rating, or "pads"
    pins: list[Pin] = Field(min_length=1)

    @field_validator("pins")
    @classmethod
    def _names_once(cls, pins: list[Pin]) -> list[Pin]:
        seen = set()
        for pin in pins:
            if pin.name in seen:
                raise ValueError(f"pin {pin.name} is listed twice on one connector")
            seen.add(pin.name)
        return pins


class Draw(Strict):
    """Current the part takes in through one pin, across the voltage range it runs on."""

    pin: str
    min_v: float = Field(gt=0)
    max_v: float = Field(gt=0)
    typical_a: float = Field(ge=0)
    worst_a: float = Field(ge=0)  # stalled, flat out, transmitting: whatever its worst case is
    note: str | None = None

    @model_validator(mode="after")
    def _sensible(self):
        if self.min_v >= self.max_v:
            raise ValueError(f"draw on {self.pin}: min_v should be below max_v")
        if self.typical_a > self.worst_a:
            raise ValueError(f"draw on {self.pin}: worst_a can't be less than typical_a")
        return self


class Output(Strict):
    """A supply on the part: a regulator, a BEC, or a rail it passes through."""

    name: str = Field(pattern=NAME)
    # switching: input power is output power over the efficiency; linear: the input current is
    # the output current; through: the same rail, passed straight on
    kind: Literal["switching", "linear", "through"] = "switching"
    pins: list[str] = Field(min_length=1)  # where it comes out
    fed_from: str | None = None  # the pin feeding it
    volts: float = Field(gt=0)
    continuous_a: float = Field(gt=0)
    peak_a: float | None = Field(default=None, gt=0)
    own_a: float = Field(default=0, ge=0)  # what the part itself takes from it
    efficiency: float | None = Field(default=None, gt=0, le=1)

    @property
    def available(self) -> float:
        """Continuous amps left for everything else."""
        return self.continuous_a - self.own_a


class Rating(Strict):
    """What one contact of a connector carries, by the maker's numbers."""

    continuous_a: float = Field(gt=0)
    wire_awg: int | None = None  # the gauge the rating was measured on
    temp_rise_c: float | None = Field(default=None, gt=0)  # the rise at continuous_a
    contact_mohm: float | None = Field(default=None, gt=0)
    max_c: float | None = None  # the hottest it's rated for
    volts: float | None = Field(default=None, gt=0)

    @property
    def contact_resistance(self) -> float | None:
        return None if self.contact_mohm is None else units.mohm_to_ohm(self.contact_mohm)


class FuseRating(Strict):
    rated_a: float = Field(gt=0)
    cold_mohm: float = Field(gt=0)
    melting_i2t_a2s: float = Field(gt=0)

    @property
    def cold_resistance(self) -> float:
        return units.mohm_to_ohm(self.cold_mohm)


class FuseFamily(Strict):
    volts: float = Field(gt=0)
    interrupting_a: float = Field(gt=0)
    max_c: float
    ratings: list[FuseRating] = Field(min_length=1)

    @field_validator("ratings")
    @classmethod
    def _each_once(cls, ratings: list[FuseRating]) -> list[FuseRating]:
        seen = set()
        for rating in ratings:
            if rating.rated_a in seen:
                raise ValueError(f"the {rating.rated_a:g} A rating is listed twice")
            seen.add(rating.rated_a)
        return ratings

    def rating(self, amps: float) -> FuseRating:
        for rating in self.ratings:
            if rating.rated_a == amps:
                return rating
        listed = ", ".join(f"{r.rated_a:g}" for r in self.ratings)
        raise KeyError(f"there's no {amps:g} A fuse in this family (it has {listed} A)")


class ForwardPoint(Strict):
    amps: float = Field(gt=0)
    volts: float = Field(gt=0)  # the datasheet's maximum at that current


class DiodeData(Strict):
    reverse_v: float = Field(gt=0)
    continuous_a: float = Field(gt=0)
    surge_a: float | None = Field(default=None, gt=0)
    forward: list[ForwardPoint] = Field(min_length=1)

    @field_validator("forward")
    @classmethod
    def _rising(cls, points: list[ForwardPoint]) -> list[ForwardPoint]:
        for low, high in zip(points, points[1:], strict=False):
            if not (high.amps > low.amps and high.volts >= low.volts):
                raise ValueError("forward points should rise in current and in voltage")
        return points

    def forward_volts(self, amps: float) -> float:
        """The drop at a current: straight between the points on a log scale of current, and
        held at the end points outside them."""
        points = self.forward
        if amps <= points[0].amps:
            return points[0].volts
        for low, high in zip(points, points[1:], strict=False):
            if amps <= high.amps:
                share = math.log(amps / low.amps) / math.log(high.amps / low.amps)
                return low.volts + share * (high.volts - low.volts)
        return points[-1].volts


class Switch(Strict):
    """One channel of an analog switch: common joins `low` with the control pin low, and
    `high` with it high. With `enable` given and high, the channel is open."""

    control: str
    common: str
    low: str
    high: str
    enable: str | None = None


class Element(Strict):
    """A two-terminal part inside a board: a resistor soldered across two pins, a fuse in its
    holder, a diode (its `between` is anode then cathode, and the block's diode data applies)."""

    name: str = Field(pattern=NAME)
    kind: Literal["resistor", "fuse", "diode"]
    between: tuple[str, str]
    ohms: float | None = Field(default=None, gt=0)
    watts: float | None = Field(default=None, gt=0)
    note: str | None = None

    @model_validator(mode="after")
    def _resistors_say_how_much(self):
        if self.kind == "resistor" and self.ohms is None:
            raise ValueError(f"resistor {self.name} needs its ohms")
        return self


ESTIMATE = re.compile(r"^(\w+)(?:\[([^\]]+)\])?(?:\.(\w+))?$")


class ElectricalBlock(Strict):
    source: Source
    estimates: list[str] = Field(default_factory=list)
    estimate_note: str | None = None
    connectors: list[Connector] = Field(default_factory=list)
    draws: list[Draw] = Field(default_factory=list)
    outputs: list[Output] = Field(default_factory=list)
    rating: Rating | None = None  # for connector families
    fuse: FuseFamily | None = None  # for fuse families
    diode: DiodeData | None = None  # for diodes
    joined: list[list[str]] = Field(default_factory=list)  # pins that are one net on the board
    switches: list[Switch] = Field(default_factory=list)
    elements: list[Element] = Field(default_factory=list)

    @model_validator(mode="after")
    def _everything_named_is_there(self):
        names = [c.name for c in self.connectors]
        if len(names) != len(set(names)):
            raise ValueError("two connectors share a name")
        refs = {ref for ref, _ in self.pins()}
        for draw in self.draws:
            self._known(draw.pin, refs, "draws")
        for output in self.outputs:
            for ref in output.pins:
                self._known(ref, refs, f"output {output.name}")
            if output.fed_from is not None:
                self._known(output.fed_from, refs, f"output {output.name}")
        for n, switch in enumerate(self.switches, start=1):
            for ref in (switch.control, switch.common, switch.low, switch.high, switch.enable):
                if ref is not None:
                    self._known(ref, refs, f"switch {n}")
        for group in self.joined:
            for ref in group:
                self._known(ref, refs, "joined")
        names = [e.name for e in self.elements]
        if len(names) != len(set(names)):
            raise ValueError("two elements share a name")
        for element in self.elements:
            for ref in element.between:
                self._known(ref, refs, f"element {element.name}")
            if element.kind == "diode" and self.diode is None:
                raise ValueError(
                    f"element {element.name} is a diode, so the block needs diode data"
                )
        for path in self.estimates:
            if not self._resolves(path):
                raise ValueError(f"estimates names {path}, which isn't in this block")
        if self.estimates and not self.estimate_note:
            raise ValueError("estimates need an estimate_note saying how they were worked out")
        return self

    @staticmethod
    def _known(ref: str, refs: set[str], where: str):
        if ref not in refs:
            listed = ", ".join(sorted(refs)) or "none"
            raise ValueError(f"{where}: {ref} isn't a pin (the pins are {listed})")

    def _resolves(self, path: str) -> bool:
        match = ESTIMATE.match(path)
        if not match:
            return False
        section, key, field = match.groups()
        if section in ("rating", "fuse", "diode"):
            value = getattr(self, section)
            if key is not None or value is None:
                return False
            return field is None or field in type(value).model_fields
        items = {
            "connectors": {c.name: c for c in self.connectors},
            "draws": {d.pin: d for d in self.draws},
            "outputs": {o.name: o for o in self.outputs},
            "elements": {e.name: e for e in self.elements},
        }.get(section)
        if items is None or key not in items:
            return False
        return field is None or field in type(items[key]).model_fields

    def pins(self) -> Iterator[tuple[str, Pin]]:
        for connector in self.connectors:
            for pin in connector.pins:
                yield f"{connector.name}.{pin.name}", pin

    def pin(self, ref: str) -> Pin:
        for name, pin in self.pins():
            if name == ref:
                return pin
        raise KeyError(f"{ref} isn't a pin on this part")

    def connector(self, name: str) -> Connector:
        for connector in self.connectors:
            if connector.name == name:
                return connector
        raise KeyError(f"{name} isn't a connector on this part")

    def output(self, name: str) -> Output:
        for output in self.outputs:
            if output.name == name:
                return output
        raise KeyError(f"{name} isn't a supply on this part")

    def element(self, name: str) -> Element:
        for element in self.elements:
            if element.name == name:
                return element
        raise KeyError(f"{name} isn't an element on this part")

    def families(self) -> set[str]:
        return {c.family for c in self.connectors if c.family != PADS}
