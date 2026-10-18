"""One motor and prop from its thrust table, and the whole drone's power at any speed.

Hover: the electrical power for a thrust comes straight from the table (power = volts x amps
at the table's voltage). For a given thrust the prop needs about the same speed and torque
whatever the battery voltage, so the power stays the same and only the current changes with
voltage. The battery model turns that power into current, sag included.

Full throttle: the motor's speed scales with voltage, so thrust scales with voltage squared
and power with voltage cubed. On a real pack the voltage sags as the current climbs, so the
pack settles where V = V_rest - R * P0 * V^2 / V0^3, which has a closed-form answer.

Current cap: if the build's firmware caps the pack current and flat out would pull more, the
flight controller throttles back until the pack gives exactly the cap. The pack then sits at
V_rest - R * cap, the motors get V * cap watts, and thrust follows that power to the 2/3,
the same law as above, so the capped and uncapped numbers meet without a jump.

Forward flight: each prop's power splits into lifting (induced) power, which shrinks with
speed because the prop keeps getting fresh air; blade-drag (profile) power, which grows a
little with speed; and the power to push the drone through the air, drag x speed. The hover
table fixes the total at zero speed, and two textbook numbers split it: real rotors need
about 15% more induced power than ideal momentum theory (INDUCED_FACTOR), and blade drag
takes about a quarter of a small prop's shaft power in a hover (PROFILE_SHARE). That split
also gives the motor and ESC's efficiency, which the drag power goes through too. The
inflow through a tilted prop in forward flight comes from Glauert's momentum theory.

Pessimistic data: thrust tables run optimistic, so the pessimistic case scales every thrust
in the table down (DERATE), which means more power for the same thrust and less thrust at
full throttle. A 10% cut costs about 15% of the flight time.
"""

import bisect
import math
from dataclasses import dataclass, field

from pcs14.catalog import Prop, SourceKind, ThrustTable
from pcs14.design import Build
from pcs14.sizing.battery import Pack
from pcs14.sizing.drag import AIR_DENSITY, drag_force
from pcs14.units import newton_to_gram_force

DERATE = {
    SourceKind.THRUST_STAND: 0.02,
    SourceKind.INDEPENDENT_TEST: 0.05,
    SourceKind.MANUFACTURER: 0.10,
    SourceKind.ESTIMATE: 0.15,
    SourceKind.MADE_UP: 0.10,
}
MOTORS = 4
INDUCED_FACTOR = 1.15  # real rotors vs ideal momentum theory
PROFILE_SHARE = 0.25  # blade drag's share of a small prop's shaft power in a hover
PROFILE_GROWTH = 4.65  # blade-drag power grows as 1 + 4.65 x (advance ratio)^2
MAX_TILT = math.radians(45)  # how far the drone will lean to fly fast or fight wind


@dataclass(frozen=True)
class FullThrottle:
    voltage: float  # V at the pack, after sag
    current: float  # A from the pack, all four motors
    thrust: float  # N per motor
    rpm: float
    capped_from: float | None = None  # A it would pull without the firmware's current cap


@dataclass(frozen=True)
class Rotor:
    table: ThrustTable
    prop: Prop
    thrust_scale: float = 1.0  # 1 - DERATE in the pessimistic case
    current_cap: float | None = None  # A from the pack, all four motors, set in the firmware

    @classmethod
    def from_build(cls, build: Build, pessimistic: bool = False) -> "Rotor":
        table = build.thrust_table
        scale = 1 - DERATE[table.source.kind] if pessimistic else 1.0
        return cls(table=table, prop=build.prop, thrust_scale=scale, current_cap=build.current_cap)

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
        return _interpolate(self._thrusts, [r.power for r in self.table.rows], thrust, 1.5)

    def rpm_for_thrust(self, thrust: float) -> float | None:
        rpms = [r.rpm for r in self.table.rows]
        if any(rpm is None for rpm in rpms):
            return None
        return _interpolate(self._thrusts, rpms, thrust, 0.5)

    def full_throttle(self, pack: Pack, soc: float) -> FullThrottle:
        """All four motors flat out, on this pack at this state of charge."""
        v0 = self.table.voltage
        p0 = MOTORS * self.max_power
        a = pack.resistance * p0 / v0**3
        rest = pack.ocv(soc)
        volts = (-1 + math.sqrt(1 + 4 * a * rest)) / (2 * a)
        current = p0 * volts**2 / v0**3
        rpm = self.table.rows[-1].rpm or 0.0
        cap = self.current_cap
        if cap is None or current <= cap:
            return FullThrottle(
                voltage=volts,
                current=current,
                thrust=self.max_thrust * (volts / v0) ** 2,
                rpm=rpm * volts / v0,
            )
        volts = rest - pack.resistance * cap
        share = (volts * cap / p0) ** (1 / 3)  # the motors' effective voltage over v0
        return FullThrottle(
            voltage=volts,
            current=cap,
            thrust=self.max_thrust * share**2,
            rpm=rpm * share,
            capped_from=current,
        )


class CannotHover(Exception):
    """The motors can't hold this weight up, even at full throttle on the table."""


@dataclass(frozen=True)
class PowerModel:
    """The whole drone's electrical power at any airspeed, fitted to the hover table."""

    rotor: Rotor
    weight: float  # N
    drag_area: float  # m^2
    avionics_power: float = 0.0  # W: flight controller, radios, companion computer
    air_density: float = AIR_DENSITY
    hover_thrust: float = field(init=False)  # N per motor
    hover_power: float = field(init=False)  # W per motor, from the table
    hover_inflow: float = field(init=False)  # m/s through each prop
    efficiency: float = field(init=False)  # motor and ESC: shaft power over electrical
    tip_speed: float | None = field(init=False)  # m/s, from the table's rpm

    def __post_init__(self):
        thrust = self.weight / MOTORS
        power = self.rotor.power_for_thrust(thrust)
        if power is None:
            raise CannotHover(
                f"each motor would need {newton_to_gram_force(thrust):.0f} g to hover, but the "
                f"thrust table tops out at {newton_to_gram_force(self.rotor.max_thrust):.0f} g"
            )
        area = self.rotor.prop.disk_area
        inflow = math.sqrt(thrust / (2 * self.air_density * area))
        rpm = self.rotor.rpm_for_thrust(thrust)
        derived = {
            "hover_thrust": thrust,
            "hover_power": power,
            "hover_inflow": inflow,
            "efficiency": INDUCED_FACTOR * thrust * inflow / ((1 - PROFILE_SHARE) * power),
            "tip_speed": rpm * 2 * math.pi / 60 * self.rotor.prop.radius if rpm else None,
        }
        for name, value in derived.items():
            object.__setattr__(self, name, value)

    def drag(self, speed: float) -> float:
        return drag_force(self.drag_area, speed, self.air_density)

    def tilt(self, speed: float) -> float:
        """Radians from level: the lean that balances drag against weight."""
        return math.atan2(self.drag(speed), self.weight)

    def thrust_per_motor(self, speed: float) -> float:
        return math.hypot(self.drag(speed), self.weight) / MOTORS

    def induced_velocity(self, speed: float) -> float:
        """Glauert's inflow through a tilted prop moving at `speed`, by bisection."""
        thrust = self.thrust_per_motor(speed)
        area = self.rotor.prop.disk_area
        tilt = self.tilt(speed)
        along, across = speed * math.sin(tilt), speed * math.cos(tilt)
        low, high = 0.0, math.sqrt(thrust / (2 * self.air_density * area))
        for _ in range(60):
            mid = (low + high) / 2
            pushed = 2 * self.air_density * area * mid * math.hypot(across, along + mid)
            if pushed < thrust:
                low = mid
            else:
                high = mid
        return (low + high) / 2

    def power(self, speed: float) -> float:
        """Total electrical watts from the pack at `speed` m/s of airspeed."""
        thrust = self.thrust_per_motor(speed)
        inflow = self.induced_velocity(speed)
        induced = (1 - PROFILE_SHARE) * self.hover_power * (thrust * inflow)
        induced /= self.hover_thrust * self.hover_inflow
        advance = speed * math.cos(self.tilt(speed)) / self.tip_speed if self.tip_speed else 0.0
        profile = PROFILE_SHARE * self.hover_power * (1 + PROFILE_GROWTH * advance**2)
        pushing = self.drag(speed) * speed / self.efficiency
        return MOTORS * (induced + profile) + pushing + self.avionics_power

    def least_power_speed(self, top: float = 30.0, step: float = 0.1) -> tuple[float, float]:
        """The airspeed that costs the least power, and that power."""
        speeds = [round(i * step, 9) for i in range(int(round(top / step)) + 1)]
        best = min(speeds, key=self.power)
        return best, self.power(best)

    def available_thrust_per_motor(self, speed: float, full: FullThrottle) -> float:
        """Full-throttle thrust, falling off as air rushes through the prop toward its pitch
        speed (rpm x pitch), where it would make none."""
        pitch_speed = full.rpm * self.rotor.prop.pitch / 60
        if pitch_speed <= 0:
            return full.thrust
        along = speed * math.sin(self.tilt(speed))
        return full.thrust * max(0.0, 1 - along / pitch_speed)

    def can_fly(self, speed: float, full: FullThrottle) -> bool:
        if self.tilt(speed) > MAX_TILT:
            return False
        return self.available_thrust_per_motor(speed, full) >= self.thrust_per_motor(speed)

    def top_speed(self, full: FullThrottle, limit: float = 80.0, step: float = 0.1) -> float:
        """The fastest airspeed it can hold with this much full-throttle thrust."""
        if not self.can_fly(0.0, full):
            return 0.0
        top = 0.0
        for i in range(1, int(round(limit / step)) + 1):
            if not self.can_fly(i * step, full):
                break
            top = round(i * step, 9)
        return top


def _interpolate(xs: list[float], ys: list[float], x: float, below: float) -> float | None:
    """Straight lines between the table rows. Below the first row, the value scales with
    (thrust / first row's thrust) ** `below`: momentum theory says power goes as thrust^1.5
    and rpm as thrust^0.5 for a fixed prop. Many tables start at 50% throttle, well above a
    light drone's hover, so a straight line to zero there would overstate the power a lot."""
    if x > xs[-1]:
        return None
    if x <= xs[0]:
        return ys[0] * (x / xs[0]) ** below
    i = bisect.bisect_left(xs, x)
    fraction = (x - xs[i - 1]) / (xs[i] - xs[i - 1])
    return ys[i - 1] + fraction * (ys[i] - ys[i - 1])
