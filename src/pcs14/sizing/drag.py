"""Drag from frontal area, until the aero side track has real tables.

Each part carries a drag area: its drag coefficient times its frontal area. The drone's drag
area is the frame's plus everything it carries, and drag = 1/2 rho V^2 x drag area.
"""

from pcs14.design import Build, SetupTargets

AIR_DENSITY = 1.225  # kg/m^3, standard sea-level air


def drag_area(build: Build, setup: SetupTargets) -> float:
    """Square meters, for the frame plus the base parts and the modules fitted."""
    return build.frame.drag_area + sum(part.drag_area for part in build.carried(setup.modules))


def drag_force(area: float, speed: float, air_density: float = AIR_DENSITY) -> float:
    return 0.5 * air_density * speed * speed * area
