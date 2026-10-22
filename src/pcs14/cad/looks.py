"""What the parts look like, for the pictures and the site's model: a board with its chips, its
plugs where the pins research put them and gold header pins at each pin, a motor with its base,
the gap over its windings and a bell with cooling holes, and the rest of what the catalog draws
as plain boxes and tubes: the chute's launcher, the HaLow whip, the Remote ID's case, the lidar
with its two windows, the camera's lens, the HaLow HAT with its card, the Pi's cooler with its
fan, the module couplers and the inline fuses. Each look stays inside its part's envelope
(pcs14.cad.parts), which is what the checks use, so the detail changes no check.

A look is a compound of named pieces ("board", "chips", "plugs", "pins", "antenna", "base",
"gap", "bell", "shaft", "lens", "cap", "nickel", "shield", "fan", "sleeve") so the site can give
each its own material; "body" is the part's own.
"""

import hashlib
import math

from build123d import Align, Axis, Box, Compound, Cone, Cylinder, Pos, Rot, fillet

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


def _cyl(radius_mm, height_mm, x_mm=0.0, y_mm=0.0, z_mm=0.0):
    shape = Cylinder(_mm(radius_mm), _mm(height_mm), align=BOTTOM)
    return Pos(_mm(x_mm), _mm(y_mm), _mm(z_mm)) * shape


def _rounded(length_mm, width_mm, height_mm, radius_mm, x_mm=0.0, y_mm=0.0, z_mm=0.0):
    """A box with its upright edges rounded, the way a molded case is."""
    box = Box(_mm(length_mm), _mm(width_mm), _mm(height_mm), align=BOTTOM)
    box = fillet(box.edges().filter_by(Axis.Z), _mm(radius_mm))
    return Pos(_mm(x_mm), _mm(y_mm), _mm(z_mm)) * box


def _label(shape, label: str):
    shape.label = label
    return shape


def _look(part: CatalogPart, pieces: list):
    look = Compound(children=[p for p in pieces if p is not None])
    look.label = f"{part.id} look"
    return look


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


def _chute_look(part: CatalogPart):
    """The Harrier's launcher, drawn from its shape alone (Fruity Chutes publish no drawing): a
    base flange, the tube, a dark band near its top, a narrower neck and the cap that lets go,
    with a shallow dish in it."""
    cad = part.cad
    r, length = cad.diameter_mm / 2, cad.length_mm
    base_h, neck_h, cap_h = 6.0, 1.5, 20.0
    tube_top = length - cap_h - neck_h
    cap = _cyl(r, cap_h, z_mm=length - cap_h) - _cyl(r * 0.72, 1.2, z_mm=length - 1.2)
    return _look(part, [
        _label(_cyl(r, base_h), "cap"),
        _label(_cyl(r * 0.95, tube_top - base_h, z_mm=base_h), "body"),
        _label(_cyl(r, 3.0, z_mm=tube_top - 12.0), "cap"),
        _label(_cyl(r * 0.88, neck_h, z_mm=tube_top), "cap"),
        _label(cap, "cap"),
    ])  # fmt: skip


def _whip_look(part: CatalogPart):
    """A hinged whip, from its mount end: the jack's nut, the knuckle with its pin across, and
    the whip tapering to its tip."""
    cad = part.cad
    r, length = cad.diameter_mm / 2, cad.length_mm
    pin = Pos(0, 0, _mm(11.5)) * Rot(90, 0, 0) * Cylinder(_mm(r * 0.35), _mm(2 * r), align=CENTER)
    whip = Pos(0, 0, _mm(17)) * Cone(_mm(r * 0.75), _mm(r * 0.55), _mm(length - 22), align=BOTTOM)
    return _look(part, [
        _label(_cyl(r * 0.8, 6.0), "nickel"),
        _label(_cyl(r, 11.0, z_mm=6.0), "body"),
        _label(pin, "nickel"),
        _label(whip, "body"),
        _label(_cyl(r * 0.6, 5.0, z_mm=length - 5.0), "body"),
    ])  # fmt: skip


def _case_look(part: CatalogPart):
    """A small molded case: two halves with a seam between, a label on top and an LED's window."""
    cad = part.cad
    length, width, height = cad.length_mm, cad.width_mm, cad.height_mm
    low, seam = height * 0.45, 0.7
    upper = _rounded(length, width, height - low - seam, 2.5, z_mm=low + seam)
    upper -= _box(length * 0.6, width * 0.55, 0.3, -length * 0.08, 0, height - 0.3)
    led = (length / 2 - 4.5, width / 2 - 4.5)
    upper -= _cyl(1.4, 0.8, *led, height - 0.8)
    body = [
        _rounded(length, width, low, 2.5),
        _rounded(length - 1, width - 1, seam, 2.0, z_mm=low),
        upper,
    ]
    return _look(part, [_named(body, "body"), _label(_cyl(1.1, 0.6, *led, height - 0.8), "lens")])


def _lidar_look(part: CatalogPart):
    """Benewake's TF-Luna: its two mounting ears, the housing, and the two round windows in its
    face, one it sends from and one it sees with."""
    cad = part.cad
    length, width, ears_t = cad.length_mm, cad.width_mm, cad.thickness_mm
    height = ears_t + cad.top_mm
    ears = _box(length, 9.0, ears_t, 0, 0, 0)
    for hole in cad.holes:
        ears -= Pos(hole.x, hole.y, 0) * Cylinder(hole.diameter / 2, 0.05, align=CENTER)
    body = _rounded(length - 9.0, width, height - 0.5, 1.5)
    windows = [_cyl(3.6, 0.5, x, 0, height - 0.5) for x in (-5.5, 5.5)]
    return _look(part, [_named([ears, body], "body"), _named(windows, "lens")])


def _holed_board(part: CatalogPart):
    cad = part.cad
    board = Box(_mm(cad.length_mm), _mm(cad.width_mm), _mm(cad.thickness_mm), align=BOTTOM)
    for hole in cad.holes:
        board -= Pos(hole.x, hole.y, 0) * Cylinder(hole.diameter / 2, 0.05, align=CENTER)
    return _label(board, "board")


def _camera_look(part: CatalogPart):
    """Raspberry Pi's Camera Module 3: the board and its four holes, the sensor's housing and the
    lens barrel with its glass, centered on the holes, and the ribbon's socket on the back at the
    edge the holes leave free."""
    cad = part.cad
    t, top, bottom, width = cad.thickness_mm, cad.top_mm, cad.bottom_mm, cad.width_mm
    y = sum(h.y_mm for h in cad.holes) / len(cad.holes)
    barrel = _cyl(3.8, top - 2.2, 0, y, t + 2.2) - _cyl(2.6, 0.6, 0, y, t + top - 0.6)
    socket_h = min(2.5, bottom)
    chips = [
        _box(8.5, 8.5, 2.2, 0, y, t),
        barrel,
        _box(3.0, 2.0, 0.8, 8.0, width / 2 - 4, t),
        _box(2.0, 2.0, 0.6, -8.0, width / 2 - 4, t),
    ]
    return _look(part, [
        _holed_board(part),
        _named(chips, "chips"),
        _label(_cyl(2.5, 0.4, 0, y, t + top - 0.6), "lens"),
        _label(_box(20.0, 5.0, socket_h, 0, width / 2 - 3.0, -socket_h), "plugs"),
    ])  # fmt: skip


def _hat_look(part: CatalogPart):
    """Heltec's HaLow HAT as the catalog draws it: a Pi HAT with the mini PCIe card lying in its
    socket, the card's shield can and antenna jack, a latch at its far end, a couple of chips,
    and the 40-pin header underneath."""
    cad = part.cad
    length, width, t, bottom = cad.length_mm, cad.width_mm, cad.thickness_mm, cad.bottom_mm
    socket_x = -length / 2 + 6.5
    card_len, card_z = 50.95, t + 2.6
    card_x = socket_x + card_len / 2 - 2.0
    card_end = card_x + card_len / 2
    chips = [
        _box(5.0, 32.0, 4.0, socket_x, 0, t),
        _box(5.0, 5.0, 1.0, 10.0, -22.0, t),
        _box(3.0, 2.0, 0.8, -12.0, 22.0, t),
        _box(51.0, 5.0, bottom, 0, width / 2 - 3.5, -bottom),
    ]
    shield = [
        _box(18.0, 18.0, 1.8, card_x - 6.0, 0, card_z + 0.8),
        _box(4.0, 8.0, 3.4, card_end - 2.0, 0, t),
    ]
    return _look(part, [
        _holed_board(part),
        _named([_box(card_len, 30.0, 0.8, card_x, 0, card_z)], "board"),
        _named(chips, "chips"),
        _named(shield, "shield"),
        _label(_cyl(1.0, 1.3, card_end - 7.0, 10.0, card_z + 0.8), "pins"),
    ])  # fmt: skip


def _cooler_look(part: CatalogPart):
    """Raspberry Pi's Active Cooler: the heatsink's plate and fins, and the blower in its corner
    with its round intake, its hub and blades."""
    cad = part.cad
    length, width, height = cad.length_mm, cad.width_mm, cad.height_mm
    plate_h, fan_len = 2.5, 26.0
    fan_x = -length / 2 + fan_len / 2
    fin_len = length - fan_len - 1.0
    fin_x = length / 2 - fin_len / 2
    fins = [
        _box(fin_len, 1.0, height - plate_h, fin_x, -width / 2 + (k + 0.5) * width / 8, plate_h)
        for k in range(8)
    ]
    housing = _rounded(fan_len, width - 2.0, height - plate_h, 3.0, fan_x, 0, plate_h)
    housing -= _cyl(10.5, 1.2, fan_x, 0, height - 1.2)
    blade = Box(_mm(5.5), _mm(0.9), _mm(0.8), align=BOTTOM)
    blades = [
        Pos(_mm(fan_x), 0, _mm(height - 1.6)) * Rot(0, 0, 40 * k) * Pos(_mm(7.2), 0, 0) * blade
        for k in range(9)
    ]
    return _look(part, [
        _named([_box(length, width, plate_h, 0, 0, 0), *fins], "body"),
        _named([housing, _cyl(4.5, 1.0, fan_x, 0, height - 1.4), *blades], "fan"),
    ])  # fmt: skip


def _coupler_look(part: CatalogPart):
    """One slot's coupler: an XT30 half for the power with its two contacts in their holes, and an
    8-pin JST-GH beside it for CAN and the module's ID, both open toward the half they mate with."""
    cad = part.cad
    height = cad.height_mm
    down = all(c.side == "bottom" for c in cad.connectors)

    def opening(depth):  # where a hole that deep starts, from the mating face
        return 0.0 if down else height - depth

    first = {}
    for c in cad.connectors:
        first.setdefault(c.name.split("_")[-1], c)
    power = list(first["POWER"].pins.values())
    signal = list(first["SIGNAL"].pins.values())
    px, sx = power[0][0], signal[0][0]
    xt30 = _rounded(7.5, 11.5, height, 1.5, px, 0, 0)
    gh = _box(4.6, 11.0, height, sx, 0, 0)
    contacts = []
    for _, y in power:
        xt30 -= _cyl(1.25, 3.0, px, y, opening(3.0))
        contacts.append(_cyl(0.55, 2.6, px, y, 0.4 if down else height - 3.0))
    for _, y in signal:
        gh -= _box(0.8, 0.8, 2.0, sx, y, opening(2.0))
        contacts.append(_box(0.5, 0.5, 1.6, sx, y, 0.4 if down else height - 2.0))
    return _look(part, [_label(xt30, "body"), _label(gh, "plugs"), _named(contacts, "pins")])


def _fuse_look(part: CatalogPart):
    """An inline MINI fuse: the violet body, its blades soldered to the wires, and each joint
    under black heat shrink."""
    height = part.cad.height_mm
    half = 10.9 / 2
    blades = [_box(2.55, 2.6, 0.6, side * (half + 1.275), 0, height / 2 - 0.3) for side in (-1, 1)]
    shrink = [_rounded(7.5, 6.0, 4.0, 1.5, side * 11.25, 0, 0.5) for side in (-1, 1)]
    return _look(part, [
        _label(_box(10.9, 8.7, 3.8, 0, 0, (height - 3.8) / 2), "body"),
        _named(blades, "nickel"),
        _named(shrink, "sleeve"),
    ])  # fmt: skip


# the parts the catalog draws as plain boxes and tubes that have a look of their own
OWN_LOOKS = {
    "fruity-chutes-harrier-40-42": _chute_look,
    "halow-antenna-915": _whip_look,
    "ruko-r111": _case_look,
    "benewake-tf-luna": _lidar_look,
    "rpi-camera-module-3": _camera_look,
    "heltec-ht-hc01p": _hat_look,
    "rpi-active-cooler": _cooler_look,
    "module-socket": _coupler_look,
    "module-plug": _coupler_look,
    "branch-fuses": _fuse_look,
}


def look_for(part: CatalogPart):
    """The part's look, or None where its plain shape is all there is to it."""
    cad = part.cad
    if cad is None:
        return None
    if cad.shape == "motor":
        return _motor_look(part)
    if part.id in OWN_LOOKS:
        return OWN_LOOKS[part.id](part)
    if (
        cad.connectors
        and part.id not in NOT_BOARDS
        and (cad.shape == "board" or part.id in BREAKOUTS)
    ):
        return _board_look(part)
    return None
