"""What the parts look like, for the pictures and the site's model: a board with its chips, its
plugs where the pins research put them and gold header pins at each pin, and a motor with its
base, the gap over its windings and a bell with cooling holes. Each look stays inside its part's
envelope (pcs14.cad.parts), which is what the checks use, so the detail changes no check.

A look is a compound of named pieces ("board", "chips", "plugs", "pins", "antenna", "base",
"gap", "bell", "shaft") so the site can give each its own material.
"""

import hashlib
import math

from build123d import Align, Box, Compound, Cylinder, Pos, Rot

from pcs14 import units
from pcs14.catalog import Part as CatalogPart

BOTTOM = (Align.CENTER, Align.CENTER, Align.MIN)
CENTER = (Align.CENTER, Align.CENTER, Align.CENTER)
BOARD_MM = 1.6  # a breakout drawn as a box in the catalog: its board, under the box's height
PIN_MM = 0.64  # a header pin's square
PIN_HEIGHT_MM = 2.5
PAD_PITCH_MM = 3.5  # pads farther apart than this are solder pads, not header pins
PLUGS = {"jst-gh": (1.25, 4.25, 4.25), "jst-sh": (1.0, 2.9, 2.9)}  # pitch, depth, height in mm

# the parts the catalog draws as plain boxes that are really boards
BREAKOUTS = {
    "adafruit-lsm6dsox", "adafruit-lm66200", "pololu-d36v6f3", "cjmcu-5018",
    "bat54c-on-adapter", "p-chute-switch", "safety-monitor-buffers", "radiomaster-rp2-v2",
    "matek-bec12s-pro", "ark-gps", "ark-cannode",
}  # fmt: skip
ROUND = {"ark-gps"}  # a disk, not a rectangle
NOT_BOARDS = {"benewake-tf-luna"}  # drawn as a board in the catalog, but it's a housing
ANTENNAS = {"ark-gps": (25, 25, 4), "radiomaster-rp2-v2": (3, 8, 5)}  # the ceramic part on top, mm


def _mm(v: float) -> float:
    return units.mm_to_m(v)


def _named(children: list, label: str):
    if not children:
        return None
    group = Compound(children=children)
    group.label = label
    return group


def _box(length_mm, width_mm, height_mm, x_mm, y_mm, z_mm, turn_deg=0.0, align=BOTTOM):
    shape = Box(_mm(length_mm), _mm(width_mm), _mm(height_mm), align=align)
    return Pos(_mm(x_mm), _mm(y_mm), _mm(z_mm)) * Rot(0, 0, turn_deg) * shape


def _sizes(part: CatalogPart):
    """The board's length and width, its thickness, and the room above and below it, in mm."""
    cad = part.cad
    if cad.shape == "board":
        return cad.length_mm, cad.width_mm, cad.thickness_mm, cad.top_mm, cad.bottom_mm
    return cad.length_mm, cad.width_mm, BOARD_MM, cad.height_mm - BOARD_MM, 0.0


def _families(part: CatalogPart) -> dict:
    return {c.name: c.family for c in (part.electrical.connectors if part.electrical else [])}


def _chips(part: CatalogPart, length, width, base, room) -> list:
    """A main chip and a few small ones, laid out the same way each time for a part."""
    seed = int(hashlib.sha256(part.id.encode()).hexdigest(), 16)
    side = min(length, width) * 0.3
    tall = min(1.0, room * 0.8)
    chips = [
        _box(
            side,
            side,
            tall,
            length * (((seed % 7) - 3) / 20),
            width * (((seed // 7 % 5) - 2) / 20),
            base,
        )
    ]
    for k in range(3):
        s = side * (0.35 + 0.1 * ((seed >> (k * 3)) % 3))
        x = length * (0.3 if k != 1 else -0.3) * (1 if (seed >> k) % 2 else -1)
        y = width * (0.25 if k != 2 else -0.25)
        chips.append(_box(s, s * 0.7, tall * 0.7, x, y, base))
    return chips


def _inside(x, y, half_x, half_y, length, width):
    """A center moved just enough that something half_x by half_y around it stays on the board."""
    return (min(max(x, -length / 2 + half_x), length / 2 - half_x),
            min(max(y, -width / 2 + half_y), width / 2 - half_y))  # fmt: skip


def _plug(connector, family, base, room, under, length, width) -> object | None:
    pitch, depth, height = PLUGS[family]
    points = list(connector.pins.values())
    (x0, y0), (x1, y1) = points[0], points[-1]
    cx = sum(p[0] for p in points) / len(points)
    cy = sum(p[1] for p in points) / len(points)
    turn = math.atan2(y1 - y0, x1 - x0) if len(points) > 1 else 0.0
    long = len(points) * pitch + 2.5
    tall = min(height, room)
    if tall <= 0.2:
        return None
    z = base - tall if under else base
    # the housing's long side along the row of pins, its depth square to it, all on the board
    half_x = (abs(long * math.cos(turn)) + abs(depth * math.sin(turn))) / 2
    half_y = (abs(long * math.sin(turn)) + abs(depth * math.cos(turn))) / 2
    cx, cy = _inside(cx, cy, half_x, half_y, length, width)
    return _box(long, depth, tall, cx, cy, z, math.degrees(turn))


def _board_look(part: CatalogPart):
    length, width, thickness, top, bottom = _sizes(part)
    if part.id in ROUND:
        board = Cylinder(_mm(min(length, width) / 2), _mm(thickness), align=BOTTOM)
    else:
        board = Box(_mm(length), _mm(width), _mm(thickness), align=BOTTOM)
    for hole in getattr(part.cad, "holes", []):
        board -= Pos(hole.x, hole.y, _mm(thickness / 2)) * Cylinder(
            hole.diameter / 2, 0.05, align=CENTER
        )
    board.label = "board"
    families = _families(part)
    plugs, pins = [], []
    for c in part.cad.connectors:
        family = families.get(c.name, "pads")
        under = c.side == "bottom"
        base, room = (0.0, bottom) if under else (thickness, top)
        if family in PLUGS:
            plug = _plug(c, family, base, room, under, length, width)
            if plug is not None:
                plugs.append(plug)
            continue
        points = list(c.pins.values())
        spacing = math.dist(points[0], points[1]) if len(points) > 1 else 0.0
        for x, y in points:
            if spacing >= PAD_PITCH_MM:
                x, y = _inside(x, y, 1.2, 1.2, length, width)
                pins.append(_box(2.4, 2.4, 0.15, x, y, thickness))  # a solder pad
            else:
                x, y = _inside(x, y, PIN_MM / 2, PIN_MM / 2, length, width)
                tall = min(PIN_HEIGHT_MM, max(room, 0.3))
                pins.append(_box(PIN_MM, PIN_MM, tall, x, y, -tall if under else thickness))
    chips = _chips(part, length, width, thickness, top) if top > 0.4 else []
    antenna = None
    if part.id in ANTENNAS:
        a, b, h = ANTENNAS[part.id]
        x = length / 2 - a / 2 - 1 if part.id != "ark-gps" else 0.0
        antenna = _named([_box(a, b, min(h, top), x, 0, thickness)], "antenna")
        if part.id == "ark-gps":
            chips = [c for c in chips if abs(c.center().X) > _mm(13) or abs(c.center().Y) > _mm(13)]
    pieces = [board, _named(chips, "chips"), _named(plugs, "plugs"), _named(pins, "pins"), antenna]
    look = Compound(children=[p for p in pieces if p is not None])
    look.label = f"{part.id} look"
    return look


def _motor_look(part: CatalogPart):
    """The base with its screw holes, a narrower gap over the windings, the bell with a ring of
    cooling holes in its top, and the shaft."""
    cad = part.cad
    radius = cad.size("diameter_mm") / 2
    body = cad.size("bell_length_mm")
    base_h, gap_h = 0.004, 0.0025
    base = Cylinder(radius * 0.94, base_h, align=BOTTOM)
    half = cad.size("mount_spacing_mm") / 2
    for x, y in ((half, half), (-half, half), (-half, -half), (half, -half)):
        base -= Pos(x, y, 0) * Cylinder(cad.size("mount_hole_mm") / 2, 0.003, align=BOTTOM)
    base.label = "base"
    gap = Pos(0, 0, base_h) * Cylinder(radius * 0.82, gap_h, align=BOTTOM)
    gap.label = "gap"
    bell = Pos(0, 0, base_h + gap_h) * Cylinder(radius, body - base_h - gap_h, align=BOTTOM)
    for k in range(6):
        a = k * math.pi / 3
        hole = Cylinder(radius * 0.16, 0.003, align=BOTTOM)
        bell -= Pos(radius * 0.58 * math.cos(a), radius * 0.58 * math.sin(a), body - 0.0015) * hole
    # slots round the bell's side, over the windings
    for k in range(12):
        slot = Box(0.004, radius * 0.4, 0.006, align=CENTER)
        bell -= Rot(0, 0, k * 30) * Pos(radius, 0, base_h + gap_h + 0.006) * slot
    bell.label = "bell"
    shaft = Pos(0, 0, body) * Cylinder(
        cad.size("shaft_diameter_mm") / 2, cad.size("length_mm") - body, align=BOTTOM
    )
    shaft.label = "shaft"
    look = Compound(children=[base, gap, bell, shaft])
    look.label = f"{part.id} look"
    return look


def look_for(part: CatalogPart):
    """The part's look, or None where its plain shape is all there is to it."""
    cad = part.cad
    if cad is None:
        return None
    if cad.shape == "motor":
        return _motor_look(part)
    if (
        cad.connectors
        and part.id not in NOT_BOARDS
        and (cad.shape == "board" or part.id in BREAKOUTS)
    ):
        return _board_look(part)
    return None
