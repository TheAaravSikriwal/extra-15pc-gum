"""Mass properties: each piece's weight spread evenly over its solid, then added up into one
weight, center of gravity and inertia (about the center of gravity, in kg m²).

`budget=True` uses what the sizing model counts for each piece instead of the CAD's own
numbers, which is how the two get checked against each other.
"""

from dataclasses import dataclass

import numpy as np
from build123d import CenterOf


@dataclass(frozen=True)
class MassProperties:
    mass: float  # kg
    center: tuple[float, float, float]  # m
    inertia: tuple[tuple[float, float, float], ...]  # kg m², about the center


def mass_properties(pieces, budget: bool = False) -> MassProperties:
    total = 0.0
    moment = np.zeros(3)
    parts = []
    for piece in pieces:
        mass = piece.budget_mass if budget else piece.mass
        if mass <= 0:
            continue
        solid = piece.solid
        volume = solid.volume
        center = solid.center(CenterOf.MASS)
        c = np.array([center.X, center.Y, center.Z])
        own = np.array(solid.matrix_of_inertia) * (mass / volume)
        parts.append((mass, c, own))
        total += mass
        moment += mass * c
    if total == 0:
        return MassProperties(0.0, (0.0, 0.0, 0.0), ((0.0,) * 3,) * 3)
    cg = moment / total
    inertia = np.zeros((3, 3))
    for mass, c, own in parts:
        d = c - cg
        inertia += own + mass * (np.dot(d, d) * np.eye(3) - np.outer(d, d))
    return MassProperties(
        mass=total,
        center=tuple(float(v) for v in cg),
        inertia=tuple(tuple(float(v) for v in row) for row in inertia),
    )
