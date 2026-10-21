"""Textbook beams and joints, in SI units throughout.

An arm is a rectangular cantilever: clamped where it leaves the body plates, its motor and prop
at the tip. Euler-Bernoulli bending for its stress and deflection under a tip load; its first
bending mode with 24% of its own mass lumped at the tip (Rayleigh's share for a uniform
cantilever, good to about 1% against the exact answer once the tip mass is bigger than the
arm). The two directions bend about different axes: vertical (the thrust's way) through the
arm's thickness, in-plane through its width.
"""

import math
from dataclasses import dataclass

RAYLEIGH_SHARE = 0.24  # the share of a cantilever's own mass that acts at its tip


@dataclass(frozen=True)
class Arm:
    length_m: float  # free, from the clamp to the motor's axis
    width_m: float  # in the frame's plane
    thickness_m: float  # vertical
    density_kg_m3: float
    tip_mass_kg: float  # the motor, the prop and their screws

    @property
    def mass(self) -> float:
        return self.density_kg_m3 * self.width_m * self.thickness_m * self.length_m

    def second_moment(self, vertical: bool = True) -> float:
        """m^4: bending vertically (through the thickness) or in the frame's plane."""
        b, h = (self.width_m, self.thickness_m) if vertical else (self.thickness_m, self.width_m)
        return b * h**3 / 12

    def root_stress(self, tip_force_n: float) -> float:
        """Pa, the bending stress at the clamp under a vertical tip force."""
        return tip_force_n * self.length_m * (self.thickness_m / 2) / self.second_moment()

    def tip_deflection(self, tip_force_n: float, modulus_pa: float) -> float:
        """m, the tip's sag under a vertical tip force."""
        return tip_force_n * self.length_m**3 / (3 * modulus_pa * self.second_moment())

    def first_mode_hz(self, modulus_pa: float, vertical: bool = True) -> float:
        stiffness = 3 * modulus_pa * self.second_moment(vertical) / self.length_m**3
        mass = self.tip_mass_kg + RAYLEIGH_SHARE * self.mass
        return math.sqrt(stiffness / mass) / (2 * math.pi)


def excitations_hz(rad_s: float, blades: int) -> tuple[float, float]:
    """What a spinning prop shakes the arm at: once a turn (an unbalanced prop or motor) and
    once a blade (each blade passing the arm)."""
    turn = rad_s / (2 * math.pi)
    return turn, turn * blades


def crossing_rad_s(mode_hz: float, per_turn: int = 1) -> float:
    """The motor speed whose `per_turn`-th excitation sits on a mode."""
    return mode_hz * 2 * math.pi / per_turn


# --- joints -------------------------------------------------------------------------------


@dataclass(frozen=True)
class Joint:
    name: str
    count: int  # fasteners sharing the load
    each_n: tuple[float, float]  # (low, high) estimate of what one holds, N
    note: str

    def margin(self, load_n: float, share: float = 0.5) -> tuple[float, float]:
        """(low, high) margins: what the joint holds over the load, with only `share` of the
        fasteners carrying it (prying and uneven fits: half of them, by default)."""
        carrying = max(1, round(self.count * share))
        low, high = self.each_n
        return carrying * low / load_n, carrying * high / load_n


def screw_tension_n(stress_area_mm2: float, strength_mpa: float) -> float:
    return stress_area_mm2 * strength_mpa
