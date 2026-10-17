"""One motor and prop, from its thrust table.

Hover: the electrical power for a thrust comes straight from the table (power = volts x amps
at the table's voltage). For a given thrust the prop needs about the same speed and torque
whatever the battery voltage, so the power stays the same and only the current changes with
voltage. The battery model turns that power into current, sag included.

Full throttle: the motor's speed scales with voltage, so thrust scales with voltage squared
and power with voltage cubed. On a real pack the voltage sags as the current climbs, so the
pack settles where V = V_rest - R * P0 * V^2 / V0^3, which has a closed-form answer.

Pessimistic data: thrust tables run optimistic, so the pessimistic case scales every thrust
in the table down (DERATE), which means more power for the same thrust and less thrust at
full throttle. A 10% cut costs about 15% of the flight time.
"""

import bisect
import math
from dataclasses import dataclass

from pcs14.catalog import Prop, SourceKind, ThrustTable
from pcs14.design import Build
from pcs14.sizing.battery import Pack

DERATE = {
    SourceKind.THRUST_STAND: 0.02,
    SourceKind.INDEPENDENT_TEST: 0.05,
    SourceKind.MANUFACTURER: 0.10,
    SourceKind.ESTIMATE: 0.15,
    SourceKind.MADE_UP: 0.10,
}
MOTORS = 4


@dataclass(frozen=True)
class FullThrottle:
    voltage: float  # V at the pack, after sag
    current: float  # A from the pack, all four motors
    thrust: float  # N per motor
    rpm: float


@dataclass(frozen=True)
class Rotor:
    table: ThrustTable
    prop: Prop
    thrust_scale: float = 1.0  # 1 - DERATE in the pessimistic case

    @classmethod
    def from_build(cls, build: Build, pessimistic: bool = False) -> "Rotor":
        table = build.thrust_table
        scale = 1 - DERATE[table.source.kind] if pessimistic else 1.0
        return cls(table=table, prop=build.prop, thrust_scale=scale)

    @property
    def _thrusts(self) -> list[float]:
        return [row.thrust * self.thrust_scale for row in self.table.rows]

    @property
    def max_thrust(self) -> float:
        """N per motor at full throttle, at the table's voltage."""
        return self._thrusts[-1]

    @property
    def max_power(self) -> float:
        """W per motor at full throttle, at the table's voltage."""
        return self.table.rows[-1].power

    def power_for_thrust(self, thrust: float) -> float | None:
        """Electrical watts for one motor to make `thrust` newtons, or None if it can't."""
        return _interpolate(self._thrusts, [r.power for r in self.table.rows], thrust)

    def rpm_for_thrust(self, thrust: float) -> float | None:
        rpms = [r.rpm for r in self.table.rows]
        if any(rpm is None for rpm in rpms):
            return None
        return _interpolate(self._thrusts, rpms, thrust)

    def full_throttle(self, pack: Pack, soc: float) -> FullThrottle:
        """All four motors flat out, on this pack at this state of charge."""
        v0 = self.table.voltage
        p0 = MOTORS * self.max_power
        a = pack.resistance * p0 / v0**3
        rest = pack.ocv(soc)
        volts = (-1 + math.sqrt(1 + 4 * a * rest)) / (2 * a)
        last = self.table.rows[-1]
        return FullThrottle(
            voltage=volts,
            current=p0 * volts**2 / v0**3,
            thrust=self.max_thrust * (volts / v0) ** 2,
            rpm=(last.rpm or 0.0) * volts / v0,
        )


def _interpolate(xs: list[float], ys: list[float], x: float) -> float | None:
    """Straight lines between the table rows, heading to zero below the first row."""
    if x > xs[-1]:
        return None
    if x <= xs[0]:
        return ys[0] * x / xs[0]
    i = bisect.bisect_left(xs, x)
    fraction = (x - xs[i - 1]) / (xs[i] - xs[i - 1])
    return ys[i - 1] + fraction * (ys[i] - ys[i - 1])
