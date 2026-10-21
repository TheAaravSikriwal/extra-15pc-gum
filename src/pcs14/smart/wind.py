"""Wind sensing (#10) and the "turn back now" battery warning.

Holding still in a steady wind, the drone leans until the sideways part of its thrust matches
the drag: m g tan(tilt) = 1/2 rho CdA w^2. So the lean and the drone's drag area (the sizing
model's number) give the wind's speed, and the lean's direction gives where it's from: the
drone leans into it. Software only, nothing new on the drone.

The warning is the energy home against that wind: the power at the airspeed it flies home at
(the sizing model's curve), for as long as the ground speed toward home makes it take, against
what's left above the reserve, with a margin. It never counts on flying being cheaper than
hovering (never_below_hover).
"""

import math
from dataclasses import dataclass

from pcs14.flight.drag import G
from pcs14.sizing.drag import AIR_DENSITY

MARGIN = 1.25  # turn back while there's a quarter more than the way home needs


@dataclass(frozen=True)
class Wind:
    toward_north: float  # m/s, the way the air moves
    toward_east: float

    @property
    def speed_ms(self) -> float:
        return math.hypot(self.toward_north, self.toward_east)

    @property
    def from_deg(self) -> float:
        """Where it blows from, clockwise from north."""
        return math.degrees(math.atan2(-self.toward_east, -self.toward_north)) % 360


def from_lean(lean_north: float, lean_east: float, mass_kg: float, drag_area_m2: float,
              rho: float = AIR_DENSITY) -> Wind:  # fmt: skip
    """The wind from the thrust axis's horizontal part (the unit vector's north and east, so
    sin of the tilt in all), holding still."""
    horizontal = math.hypot(lean_north, lean_east)
    if horizontal == 0:
        return Wind(0.0, 0.0)
    tilt = math.asin(min(horizontal, 1.0))
    drag = mass_kg * G * math.tan(tilt)
    speed = math.sqrt(2 * drag / (rho * drag_area_m2))
    # it leans into the wind: the air moves the other way
    return Wind(-speed * lean_north / horizontal, -speed * lean_east / horizontal)


def energy_home_wh(power, distance_m: float, home_north: float, home_east: float,
                   wind_north: float, wind_east: float, airspeed_ms: float) -> float:  # fmt: skip
    """Wh to fly `distance_m` home (the unit vector `home_*`) at `airspeed_ms` through the wind;
    `power(airspeed)` in W. Infinite when the wind is faster than the airspeed home."""
    tail = wind_north * home_north + wind_east * home_east
    ground = airspeed_ms + tail
    if ground <= 0:
        return math.inf
    return power(airspeed_ms) * (distance_m / ground) / 3600.0


def never_below_hover(power):
    """The power curve the warning uses: the model's, but never less than hovering. Real rotors
    do get cheaper in forward flight (the sizing model's curve dips), and Gazebo's don't, so the
    sim draws its hover power flying home whatever the speed; a warning that counted on the dip
    would be optimistic exactly when being wrong strands the drone."""
    hover = power(0.0)
    return lambda speed: max(power(speed), hover)


def turn_back(remaining_wh: float, reserve_wh: float, home_wh: float,
              margin: float = MARGIN) -> bool:  # fmt: skip
    return remaining_wh - reserve_wh <= margin * home_wh
