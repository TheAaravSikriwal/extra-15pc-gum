"""Soar mode's lift detector (#31): rising air, found by comparing the thrust it takes to hold
height against what it takes in still air. The same comparison wind sensing makes sideways.

Two physics apply, and only one of them is in Gazebo. Rising air pushes on the drone's body
(1/2 rho CdA w^2), which is all Gazebo has: its rotors take their thrust from the drone's own
speed, not the air's. On a real drone the bigger effect is on the rotors: hovering in air rising
at w is descending through it at w, and to first order by momentum theory that saves the thrust
times w in power. So in the sim the detector finds the column by the small push on the body,
and the saving is the momentum-theory number, on the unproven list until a real flight.
"""

import math

from pcs14.sizing.drag import AIR_DENSITY

NOISE_FACTOR = 3.0  # a deficit this many standard errors past zero counts as lift


def thrust_n(rotor_speeds, motor_constant: float) -> float:
    return motor_constant * sum(w * w for w in rotor_speeds)


def updraft_in_sim(deficit_n: float, drag_area_m2: float, rho: float = AIR_DENSITY) -> float:
    """m/s of rising air that takes `deficit_n` of thrust off the hover, by the push on the body
    alone (Gazebo's physics)."""
    if deficit_n <= 0:
        return 0.0
    return math.sqrt(2 * deficit_n / (rho * drag_area_m2))


def power_saving_w(thrust_n: float, updraft_ms: float) -> float:
    """W a real rotor saves hovering in rising air, to first order: the thrust times the air's
    upward speed."""
    return thrust_n * max(updraft_ms, 0.0)


def standard_error(still, lifted) -> float:
    """The standard error of the difference between two hovers' mean thrusts: the hover wobbles
    from sample to sample far more than the column changes it, so it's the averages that count."""
    import numpy as np

    still, lifted = np.asarray(still, dtype=float), np.asarray(lifted, dtype=float)
    return float(np.sqrt(still.var() / len(still) + lifted.var() / len(lifted)))


def is_lift(deficit_n: float, error_n: float) -> bool:
    return deficit_n > NOISE_FACTOR * max(error_n, 1e-9)
