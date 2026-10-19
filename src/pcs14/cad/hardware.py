"""The screws, nuts and spacers that hold the drone together.

design/cad.yaml lists them under `hardware`: what each is, its size, how many, its material, and
the part it holds, counted from the CAD's screw holes. Each one is weighed from its standard
shape: an ISO 4762 socket head screw (the head, less its hex socket, and the shank at the
thread's pitch diameter), an ISO 4032 nut (or a taller lock nut), a hex standoff or a round
spacer. Things with no standard shape (silicone grommets, a hook-and-loop patch) give their own
grams. In the CAD, each item's weight goes on the pieces of the part it holds; in the catalog,
each module's hardware is one entry (base-hardware, v-hardware, p-hardware, c-hardware).
"""

import math
from dataclasses import dataclass

MM = 0.001
HARDWARE_PARTS = {"base": "base-hardware", "V": "v-hardware", "P": "p-hardware", "C": "c-hardware"}


@dataclass(frozen=True)
class Size:
    d: float  # mm, nominal
    pitch_d: float  # mm, the thread's pitch diameter
    head_d: float  # mm, a socket head's diameter (ISO 4762 dk)
    head_h: float  # mm, its height (k)
    socket: float  # mm, across the hex socket's flats (s)
    socket_depth: float  # mm (t)
    nut_af: float  # mm, a nut's or standoff's across flats (ISO 4032 s)
    nut_h: float  # mm, a plain nut (ISO 4032 m)
    lock_h: float  # mm, a nylon-insert lock nut (DIN 985 h)


# ISO 4762, ISO 4032 and DIN 985 sizes; 4-40 is the inch screw in the Harrier's base
SIZES = {
    "M2": Size(2.0, 1.740, 3.8, 2.0, 1.5, 1.0, 4.0, 1.6, 2.8),
    "M2.5": Size(2.5, 2.208, 4.5, 2.5, 2.0, 1.1, 5.0, 2.0, 3.8),
    "M3": Size(3.0, 2.675, 5.5, 3.0, 2.5, 1.3, 5.5, 2.4, 4.0),
    "4-40": Size(2.845, 2.433, 4.65, 2.84, 2.38, 1.3, 6.35, 2.38, 3.6),
}
MALE_STUB = 6.0  # mm, the threaded stub on a male-female standoff


def _hexagon(across_flats: float) -> float:
    return math.sqrt(3) / 2 * across_flats**2


def _round(diameter: float) -> float:
    return math.pi / 4 * diameter**2


def screw_volume(size: str, length_mm: float) -> float:
    """m3. The head, less its hex socket, and the shank under it."""
    s = SIZES[size]
    head = _round(s.head_d) * s.head_h - _hexagon(s.socket) * s.socket_depth
    return (head + _round(s.pitch_d) * length_mm) * MM**3


def nut_volume(size: str, lock: bool = False) -> float:
    """m3. A hex nut, or a lock nut's full height (its nylon ring counted as metal, a little
    heavy)."""
    s = SIZES[size]
    return (_hexagon(s.nut_af) - _round(s.d)) * (s.lock_h if lock else s.nut_h) * MM**3


def standoff_volume(size: str, length_mm: float) -> float:
    """m3. A male-female hex standoff: the hex body and its threaded stub."""
    s = SIZES[size]
    body = (_hexagon(s.nut_af) - _round(s.d)) * length_mm
    return (body + _round(s.pitch_d) * MALE_STUB) * MM**3


def spacer_volume(size: str, length_mm: float) -> float:
    """m3. A round spacer, twice the screw's diameter across."""
    s = SIZES[size]
    return (_round(2 * s.d) - _round(s.d + 0.2)) * length_mm * MM**3


def item_mass(item, materials) -> float:
    """kg, for one of an item."""
    if item.grams is not None:
        return item.grams / 1000
    shapes = {
        "screw": lambda: screw_volume(item.size, item.length_mm),
        "nut": lambda: nut_volume(item.size),
        "lock nut": lambda: nut_volume(item.size, lock=True),
        "standoff": lambda: standoff_volume(item.size, item.length_mm),
        "spacer": lambda: spacer_volume(item.size, item.length_mm),
    }
    return shapes[item.what]() * materials[item.material].density


def by_part(settings) -> dict[str, float]:
    """kg of hardware on each part it holds."""
    out: dict[str, float] = {}
    for item in settings.hardware:
        out[item.holds] = out.get(item.holds, 0.0) + item.count * item_mass(
            item, settings.materials
        )
    return out


def by_module(settings, module_of: dict[str, str]) -> dict[str, float]:
    """kg of hardware in each module, by where its part sits (or the item's own module)."""
    out = {m: 0.0 for m in HARDWARE_PARTS}
    for item in settings.hardware:
        module = item.module or module_of[item.holds]
        out[module] += item.count * item_mass(item, settings.materials)
    return out


def module_of_parts(build) -> dict[str, str]:
    """Each part's module, for a part the build lists in one place."""
    out = {build.esc.id: "base", build.motor.id: "base"}
    for part in build.base:
        out.setdefault(part.id, "base")
    for module, parts in build.modules.items():
        for part in parts:
            out.setdefault(part.id, module)
    return out
