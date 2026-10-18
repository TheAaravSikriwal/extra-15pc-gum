"""Builders for bought parts: each part's cad block becomes a solid, in meters.

Every part is built in its own frame: centered on x and y, sitting on z = 0 (a board's
underside parts hang below it). The assembly places them. These are envelopes, exact on the
outside and at the mounting points and plain inside, so the checks and the mass spreading
work; the existing CAD models in the local cache are what make pictures look real.
"""

import math
from dataclasses import dataclass

from build123d import Align, Box, Compound, Cylinder, Part, Polygon, Pos, Rot, extrude

from pcs14.catalog import Cell, Prop
from pcs14.catalog import Part as CatalogPart

BOTTOM = (Align.CENTER, Align.CENTER, Align.MIN)
THROUGH = 0.05  # long enough to cut through any board here


def build_part(part: CatalogPart) -> Part:
    """The solid for a bought part, from its cad block."""
    cad = part.cad
    if cad is None:
        raise ValueError(f"{part.id} has no cad block, so it can't be modeled")
    builders = {"board": _board, "box": _box, "cylinder": _cylinder, "motor": _motor, "cell": _cell}
    if cad.shape not in builders:
        raise ValueError(f"{part.id} is a {cad.shape} part, which isn't built by build_part")
    solid = builders[cad.shape](cad)
    solid.label = part.id
    return solid


def _board(cad) -> Part:
    thickness = cad.size("thickness_mm")
    length, width = cad.size("length_mm"), cad.size("width_mm")
    solid = Box(length, width, thickness, align=BOTTOM)
    if cad.top_mm > 0:
        solid += Pos(0, 0, thickness) * Box(length, width, cad.size("top_mm"), align=BOTTOM)
    if cad.bottom_mm > 0:
        bottom = cad.size("bottom_mm")
        solid += Pos(0, 0, -bottom) * Box(length, width, bottom, align=BOTTOM)
    for hole in cad.holes:
        cutter = Cylinder(
            hole.diameter / 2, THROUGH, align=(Align.CENTER, Align.CENTER, Align.CENTER)
        )
        solid -= Pos(hole.x, hole.y, thickness / 2) * cutter
    return solid


def _box(cad) -> Part:
    return Box(cad.size("length_mm"), cad.size("width_mm"), cad.size("height_mm"), align=BOTTOM)


def _cylinder(cad) -> Part:
    return Cylinder(cad.size("diameter_mm") / 2, cad.size("length_mm"), align=BOTTOM)


def _cell(cad) -> Part:
    return _cylinder(cad)


def _motor(cad) -> Part:
    """The base and bell as one cylinder, the shaft above it, and the screw holes in the base."""
    body_height = cad.size("bell_length_mm")
    body = Cylinder(cad.size("diameter_mm") / 2, body_height, align=BOTTOM)
    shaft_length = cad.size("length_mm") - body_height
    body += Pos(0, 0, body_height) * Cylinder(
        cad.size("shaft_diameter_mm") / 2, shaft_length, align=BOTTOM
    )
    half = cad.size("mount_spacing_mm") / 2
    depth = 0.005  # how far the M3 screws go into the base
    for x, y in ((half, half), (-half, half), (-half, -half), (half, -half)):
        body -= Pos(x, y, 0) * Cylinder(cad.size("mount_hole_mm") / 2, depth, align=BOTTOM)
    return body


def prop_disk(prop: Prop) -> Part:
    """The disk the prop sweeps, as thick as its hub. The clearance checks use this."""
    disk = Cylinder(prop.diameter / 2, prop.cad.size("hub_thickness_mm"), align=BOTTOM)
    disk.label = f"{prop.id} disk"
    return disk


def prop_look(prop: Prop) -> Part:
    """A simple three-blade prop for pictures: a hub with its bore, and flat tapered blades
    set at the pitch angle three quarters of the way out. It stays inside prop_disk."""
    cad = prop.cad
    radius, hub_r = prop.diameter / 2, cad.size("hub_diameter_mm") / 2
    hub_t = cad.size("hub_thickness_mm")
    look = Cylinder(hub_r, hub_t, align=BOTTOM)
    root, tip = cad.size("blade_width_mm"), cad.size("blade_width_mm") / 4
    start, end = 0.8 * hub_r, radius - 0.001
    outline = Polygon(
        (start, -root / 2), (end, -tip / 2), (end, tip / 2), (start, root / 2), align=None
    )
    blade = extrude(outline, 0.002, both=True)
    pitch = math.degrees(math.atan(prop.pitch / (2 * math.pi * 0.75 * radius)))
    blade = Pos(0, 0, hub_t / 2) * Rot(pitch, 0, 0) * blade
    for k in range(prop.blades):
        look += Rot(0, 0, k * 360 / prop.blades) * blade
    look -= Cylinder(
        cad.size("bore_mm") / 2, THROUGH, align=(Align.CENTER, Align.CENTER, Align.CENTER)
    )
    look.label = f"{prop.id} look"
    return look


@dataclass(frozen=True)
class PackLayout:
    along: int  # cells end to end, along the drone's length (x)
    across: int  # side by side (y)
    layers: int  # stacked (z)
    length: float  # m
    width: float
    height: float
    cell_diameter: float
    cell_length: float


def pack_layout(cell: Cell, cells: int, max_length: float, max_width: float) -> PackLayout:
    """The flattest way to lay the cells down (lying along the drone) that fits the tray,
    then the smallest footprint. Low and flat keeps the legs short and the weight low."""
    d, cell_len = cell.cad.size("diameter_mm"), cell.cad.size("length_mm")
    options = []
    for along in (1, 2, 3):
        if cells % along:
            continue
        rest = cells // along
        for across in range(1, rest + 1):
            if rest % across:
                continue
            layers = rest // across
            layout = PackLayout(
                along, across, layers, along * cell_len, across * d, layers * d, d, cell_len
            )
            if layout.length <= max_length + 1e-9 and layout.width <= max_width + 1e-9:
                options.append(layout)
    if not options:
        raise ValueError(
            f"{cells} cells won't fit a {max_length * 1000:.0f} x {max_width * 1000:.0f} mm tray "
            "in any layout"
        )
    return min(options, key=lambda o: (o.height, o.length * o.width, o.along))


def pack_solid(cell: Cell, layout: PackLayout) -> Compound:
    """Every cell in the layout, lying along x, centered and sitting on z = 0."""
    d, cell_len = layout.cell_diameter, layout.cell_length
    lying = Rot(0, 90, 0) * Cylinder(
        d / 2, cell_len, align=(Align.CENTER, Align.CENTER, Align.CENTER)
    )
    cells = []
    for i in range(layout.along):
        for j in range(layout.across):
            for k in range(layout.layers):
                x = (i + 0.5) * cell_len - layout.length / 2
                y = (j + 0.5) * d - layout.width / 2
                z = (k + 0.5) * d
                cells.append(Pos(x, y, z) * lying)
    pack = Compound(cells)
    pack.label = f"{layout.along * layout.across * layout.layers} x {cell.id}"
    return pack
