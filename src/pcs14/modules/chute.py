"""The parachute's opening jolt, for the structure track: how hard the canopy pulls on the drone
as it fills.

Two numbers. The sim's: the flight sim's canopy grows its drag area in a straight line over its
opening time, so the drone's ground truth during the opening gives the pull, from how fast the
fall slows (the canopy holds the weight and decelerates the drone). That's optimistic, because
real canopies overshoot as they fill. So the other number is the textbook bound: the opening
force coefficient times the dynamic pressure at the opening times the canopy's drag area,
F = Cx q (Cd S). Cx is 1.7 for a solid flat canopy at "infinite mass", the worst case, as
Knacke's Parachute Recovery Systems Design Manual gives it. A drone this light against a canopy
this big is far from infinite mass, so the bound is high on purpose: it's what the chute mount
gets designed to.
"""

from dataclasses import dataclass

import numpy as np

from pcs14.flight.drag import G
from pcs14.sizing.drag import AIR_DENSITY

OPENING_FORCE_COEFFICIENT = 1.7  # Cx: a solid flat canopy at infinite mass (Knacke)


def opening_force_bound(speed_ms: float, canopy_area_m2: float, rho: float = AIR_DENSITY,
                        cx: float = OPENING_FORCE_COEFFICIENT) -> float:  # fmt: skip
    """N: the most a canopy of drag area `canopy_area_m2` pulls opening at `speed_ms`."""
    return cx * 0.5 * rho * speed_ms**2 * canopy_area_m2


@dataclass(frozen=True)
class Pull:
    force_n: float  # the canopy's peak pull on the drone
    g: float  # the same, in the drone's weights
    at: float  # s, when
    speed_ms: float  # how fast the drone fell as the opening began


def peak_pull(t, vz, mass_kg: float, since: float, until: float) -> Pull:
    """The canopy's peak pull between `since` and `until` (s), from the drone's vertical speed
    `vz` (m/s, up positive) over time `t`: m (dvz/dt + g), the body's own drag ignored."""
    t, vz = np.asarray(t, dtype=float), np.asarray(vz, dtype=float)
    inside = (t >= since) & (t <= until)
    rate = np.gradient(vz, t)
    pull = mass_kg * (rate + G)
    k = int(np.flatnonzero(inside)[np.argmax(pull[inside])])
    return Pull(force_n=float(pull[k]), g=float(pull[k] / (mass_kg * G)), at=float(t[k]),
                speed_ms=float(-vz[inside][0]))  # fmt: skip
