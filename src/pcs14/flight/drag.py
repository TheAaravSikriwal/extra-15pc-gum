"""The drag plugin's math, in Python. The C++ plugin in sim/plugins/pcs14_drag/ does exactly
this, and the tests here are what it's checked against.

Body drag: the drone's drag area (its drag coefficient times its frontal area, the number the
sizing model uses for that combination) against the air rushing past it, the drone's velocity
less the wind's: F = -1/2 rho |v| v. The aero track's tables replace the one number later.

The parachute: fired, it waits out its ejection delay, then its canopy opens over its opening
time, its drag area growing in a straight line to full. The canopy is sized from the chute's
rating: the drag area that holds the rated mass at the rated descent rate.
"""

import math
from dataclasses import dataclass

from pcs14.sizing.drag import AIR_DENSITY

G = 9.80665


def body_drag(area: float, velocity, wind, rho: float = AIR_DENSITY) -> tuple[float, ...]:
    """N, in the world frame: `area` in m^2, `velocity` and `wind` in m/s."""
    rel = [v - w for v, w in zip(velocity, wind, strict=True)]
    speed = math.sqrt(sum(c * c for c in rel))
    return tuple(-0.5 * rho * area * speed * c for c in rel)


def canopy_area(rated_mass: float, rated_descent: float, rho: float = AIR_DENSITY) -> float:
    """m^2: the drag area that holds `rated_mass` kg at `rated_descent` m/s."""
    return 2 * rated_mass * G / (rho * rated_descent**2)


def descent_rate(area: float, mass: float, rho: float = AIR_DENSITY) -> float:
    """m/s, steady, under a canopy of drag area `area`."""
    return math.sqrt(2 * mass * G / (rho * area))


@dataclass(frozen=True)
class Chute:
    canopy_area: float  # m^2 of drag area, fully open
    ejection_s: float
    opening_s: float

    @classmethod
    def from_part(cls, part) -> "Chute":
        p = part.parachute
        return cls(canopy_area(p.rated_mass_kg, p.rated_descent_ms), p.ejection_s, p.opening_s)

    def area(self, since_fired: float | None) -> float:
        """The canopy's drag area `since_fired` seconds after firing (None: not fired)."""
        if since_fired is None or since_fired < self.ejection_s:
            return 0.0
        share = min((since_fired - self.ejection_s) / self.opening_s, 1.0)
        return self.canopy_area * share
