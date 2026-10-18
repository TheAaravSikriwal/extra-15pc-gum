"""My own printed parts, and the module envelopes, designed in place on the drone.

Each one is a real, printable part (walls at least the printable minimum, a flat face to
print on, screw holes where they meet other parts) or, for the V housing and the parachute's
holder, a sized envelope until the modules step designs them. A part's weight comes from its
geometry times its material's density, which replaces the catalog's guesses.
"""

import math
from dataclasses import dataclass, field

from build123d import Align, Box, Compound, Cylinder, GeomType, Part, Pos, Rot

from pcs14.cad.frame import FrameModel
from pcs14.cad.locate import place_point
from pcs14.cad.parts import pack_layout
from pcs14.cad.settings import CadSettings
from pcs14.design import Build

MM = 0.001
BOTTOM = (Align.CENTER, Align.CENTER, Align.MIN)
CENTERED = (Align.CENTER, Align.CENTER, Align.CENTER)
M3 = 3.2 * MM  # clearance holes
FIT = 0.4 * MM  # room around a part that drops into a pocket
M2 = 2.2 * MM


@dataclass(frozen=True)
class PrintedPart:
    name: str
    pieces: tuple[tuple[Part, str], ...]  # (solid, material); usually one printed piece
    material: str  # the printed material, for the print checks
    thinnest_wall: float  # m, of the printed pieces
    print_down: tuple[float, float, float]  # the direction of the face that sits on the bed
    module: str  # base, V, P or C
    catalog_id: str  # the catalog part whose weight this is (several parts can share one)
    mass: float = field(default=0.0)  # kg, filled in by build_printed

    @property
    def solid(self) -> Compound:
        shape = Compound([piece for piece, _ in self.pieces])
        shape.label = self.name
        return shape


def has_flat_base(solid, down: tuple[float, float, float], share: float = 0.2) -> bool:
    """True if the part has flat faces at its extreme along `down`, facing `down`, covering at
    least `share` of its outline seen from that side."""
    dx, dy, dz = down
    reach = max(v.X * dx + v.Y * dy + v.Z * dz for v in solid.vertices())
    area = 0.0
    for face in solid.faces():
        if face.geom_type != GeomType.PLANE:
            continue
        normal = face.normal_at()
        center = face.center()
        if normal.X * dx + normal.Y * dy + normal.Z * dz < 0.999:
            continue
        if abs(center.X * dx + center.Y * dy + center.Z * dz - reach) > 1e-7:
            continue
        area += face.area
    size = solid.bounding_box().size
    outline = {0: size.Y * size.Z, 1: size.X * size.Z, 2: size.X * size.Y}
    axis = max(range(3), key=lambda i: abs((dx, dy, dz)[i]))
    return area >= share * outline[axis]


def build_printed(build: Build, settings: CadSettings, frame: FrameModel) -> list[PrintedPart]:
    plate_t = build.frame.cad.size("plate_thickness_mm")
    pack = settings.pack
    layout = pack_layout(
        build.pack.cell,
        build.pack.cell_count,
        pack.tray_max_length_mm * MM,
        pack.tray_max_width_mm * MM,
    )
    tray_t = pack.tray_thickness_mm * MM
    pack_bottom = -tray_t - layout.height
    parts = []

    def add(name, pieces, material, wall, down, module, catalog_id):
        parts.append(PrintedPart(name, tuple(pieces), material, wall, down, module, catalog_id))

    # Landing legs: TPU posts under the arms, reaching below the pack, with a screw flange on top
    legs = settings.legs
    radius = legs.diameter_mm / 2 * MM
    top, bottom = plate_t, pack_bottom - legs.below_pack_mm * MM
    names = {
        (1, 1): "front left",
        (1, -1): "front right",
        (-1, 1): "back left",
        (-1, -1): "back right",
    }
    for x_mm, y_mm in legs.spots_mm:
        x, y = x_mm * MM, y_mm * MM
        leg = Pos(x, y, bottom) * Cylinder(radius, top - bottom, align=BOTTOM)
        flange_r = 12 * MM
        leg += Pos(x, y, top - 3 * MM) * Cylinder(flange_r, 3 * MM, align=BOTTOM)
        leg += Pos(x, y, bottom) * Cylinder(8 * MM, 3 * MM, align=BOTTOM)  # a foot
        along = math.atan2(y, x)
        for s in (1, -1):
            hx = x + s * 8.5 * MM * math.cos(along)
            hy = y + s * 8.5 * MM * math.sin(along)
            leg -= Pos(hx, hy, top - 1.5 * MM) * Cylinder(M3 / 2, 3.2 * MM, align=CENTERED)
        side = names[(int(math.copysign(1, x_mm)), int(math.copysign(1, y_mm)))]
        add(
            f"leg {side}",
            [(leg, legs.material)],
            legs.material,
            1.9 * MM,
            (0, 0, 1),
            "base",
            "landing-legs",
        )

    # Battery tray: under the bottom plate, long enough for the pack's whole slide, with strap slots
    length = layout.length + 2 * pack.slide_mm * MM
    width = layout.width + 12 * MM  # room for strap slots just outside the pack's sides
    cx = pack.x_mm * MM
    tray = Pos(cx, 0, -tray_t) * Box(length, width, tray_t, align=BOTTOM)
    for sx in (40, -40):
        for sy in (1, -1):
            slot_y = sy * (layout.width / 2 + 2.5 * MM)  # the strap wraps around the pack
            tray -= Pos(cx + sx * MM, slot_y, -tray_t / 2) * Box(
                22 * MM, 4 * MM, 1.0, align=CENTERED
            )
    for sx in (50, -50):
        for sy in (10, -10):
            tray -= Pos(cx + sx * MM, sy * MM, -tray_t / 2) * Cylinder(M3 / 2, 1.0, align=CENTERED)
    add("battery tray", [(tray, "petg_cf")], "petg_cf", 1.5 * MM, (0, 0, 1), "base", "battery-tray")

    # Module rail: on the top plate, with a pocket for each module socket that sits on it
    rail_s = settings.rail
    top_z = frame.top
    rail_len = (rail_s.to_x_mm - rail_s.from_x_mm) * MM
    rail_cx = (rail_s.to_x_mm + rail_s.from_x_mm) / 2 * MM
    rail_h = rail_s.height_mm * MM
    rail = Pos(rail_cx, 0, top_z) * Box(rail_len, rail_s.width_mm * MM, rail_h, align=BOTTOM)
    socket = next((p for p in build.base if p.id == "module-socket"), None)
    for spot in settings.spots():
        x, y, z = spot.placement.at
        if socket is None or spot.part_id != socket.id or z < top_z - 1e-6:
            continue
        rail -= Pos(x, y, top_z - 1e-4) * Box(
            socket.cad.size("length_mm") + FIT,
            socket.cad.size("width_mm") + FIT,
            rail_h + 2e-4,
            align=BOTTOM,
        )
    for hx in (rail_s.from_x_mm + 10, rail_s.to_x_mm - 10):
        for hy in (8, -8):
            rail -= Pos(hx * MM, hy * MM, top_z + rail_h / 2) * Cylinder(
                M3 / 2, 1.0, align=CENTERED
            )
    add(
        "module rail",
        [(rail, rail_s.material)],
        rail_s.material,
        2 * MM,
        (0, 0, -1),
        "base",
        "module-mount",
    )

    # GPS mast: a TPU block on the top plate, a carbon tube, and a TPU plate the GPS sits on
    mast = settings.gps_mast
    mx, my = (v * MM for v in mast.at_mm)
    block = mast.mount_size_mm * MM
    tube_r = mast.tube_diameter_mm / 2 * MM
    gps_z = top_z + mast.height_mm * MM
    mount = Pos(mx, my, top_z) * Box(block, block, 8 * MM, align=BOTTOM)
    mount -= Pos(mx, my, top_z + 2 * MM) * Cylinder(tube_r, 6 * MM + 1e-4, align=BOTTOM)
    plate = Pos(mx, my, gps_z - 3 * MM) * Box(24 * MM, 24 * MM, 3 * MM, align=BOTTOM)
    tube = Pos(mx, my, top_z + 2 * MM) * Cylinder(
        tube_r, gps_z - 3 * MM - top_z - 2 * MM, align=BOTTOM
    )
    tube -= Pos(mx, my, top_z) * Cylinder(tube_r - 1 * MM, 1.0, align=BOTTOM)
    add(
        "gps mast",
        [(mount, "tpu"), (plate, "tpu"), (tube, mast.material)],
        "tpu",
        3 * MM,
        (0, 0, -1),
        "V",
        "gps-mast",
    )

    # Lidar bracket: a plate under the bottom plate's nose, holding the TF-Luna by its ears
    lidar = next(p for p in build.base if p.id == "benewake-tf-luna")
    spot = settings.place[lidar.id]
    lx, ly, _ = spot.at
    bracket = Pos(lx, ly, -3 * MM) * Box(45 * MM, 28 * MM, 3 * MM, align=BOTTOM)
    for hole in lidar.cad.holes:
        hx, hy, _ = place_point((hole.x, hole.y, 0), spot)
        bracket -= Pos(hx, hy, -1.5 * MM) * Cylinder(M2 / 2, 1.0, align=CENTERED)
    for hy in (9, -9):
        bracket -= Pos(lx, ly + hy * MM, -1.5 * MM) * Cylinder(M3 / 2, 1.0, align=CENTERED)
    add(
        "lidar bracket",
        [(bracket, "petg_cf")],
        "petg_cf",
        3 * MM,
        (0, 0, 1),
        "base",
        "lidar-bracket",
    )

    # Remote ID mount: a low fence around the Ruko on the top plate (it's held by Velcro)
    ruko = next(p for p in build.base if p.id == "ruko-r111")
    rx, ry, _ = settings.place[ruko.id].at
    inner_x, inner_y = ruko.cad.size("length_mm") + 0.2 * MM, ruko.cad.size("width_mm") + 0.2 * MM
    wall = 2.5 * MM
    fence = Pos(rx, ry, top_z) * Box(inner_x + 2 * wall, inner_y + 2 * wall, 6 * MM, align=BOTTOM)
    fence -= Pos(rx, ry, top_z) * Box(inner_x, inner_y, 1.0, align=CENTERED)
    add("remote id mount", [(fence, "tpu")], "tpu", wall, (0, 0, -1), "base", "remote-id-mount")

    # Safety monitor carrier: a plate on the middle plate that the Teensy's sockets sit on
    teensy = next(p for p in build.base if p.id == "pjrc-teensy-41")
    tx, ty, tz = settings.place[teensy.id].at
    under = tz - teensy.cad.size("bottom_mm")
    carrier = Pos(tx, ty, frame.bay_floor) * Box(
        66 * MM, 22 * MM, under - frame.bay_floor, align=BOTTOM
    )
    for hx in (28, -28):
        carrier -= Pos(tx + hx * MM, ty, frame.bay_floor) * Cylinder(M3 / 2, 1.0, align=CENTERED)
    add(
        "safety monitor carrier",
        [(carrier, "petg_cf")],
        "petg_cf",
        3 * MM,
        (0, 0, -1),
        "base",
        "safety-monitor-carrier",
    )

    # Camera bracket: a tab screwed to the top plate's nose and a plate standing in front of the
    # body plates, with standoffs to the camera's four holes
    camera = next(p for p in build.modules["V"] if p.id == "rpi-camera-module-3")
    cspot = settings.place[camera.id]
    nose = build.frame.cad.size("body_front_mm")
    back_face, _, _ = place_point((0, 0, -camera.cad.size("bottom_mm")), cspot)
    cam_x, cam_y, cam_z = cspot.at
    stand = Pos(nose + 1.5 * MM, cam_y, (4 * MM + top_z) / 2) * Box(
        3 * MM, 28 * MM, top_z - 4 * MM, align=CENTERED
    )
    # the tab stays 20 mm wide so its corners clear the front props by 10 mm
    stand += Pos(nose - 7 * MM + 1.5 * MM, cam_y, top_z) * Box(
        17 * MM, 20 * MM, 3 * MM, align=BOTTOM
    )
    for hole in camera.cad.holes:
        hx, hy, hz = place_point((hole.x, hole.y, 0), cspot)
        post_len = back_face - (nose + 3 * MM)
        post = (
            Pos(nose + 3 * MM + post_len / 2, hy, hz)
            * Rot(0, 90, 0)
            * Cylinder(2.5 * MM, post_len, align=CENTERED)
        )
        stand += post
        stand -= Pos(nose + 3 * MM, hy, hz) * Rot(0, 90, 0) * Cylinder(M2 / 2, 0.05, align=CENTERED)
    for hx in (nose - 10 * MM,):
        for hy in (5, -5):
            stand -= Pos(hx, cam_y + hy * MM, top_z + 1.5 * MM) * Cylinder(
                M3 / 2, 1.0, align=CENTERED
            )
    add(
        "camera bracket",
        [(stand, "petg_cf")],
        "petg_cf",
        1.4 * MM,
        (0, 0, 1),
        "V",
        "camera-bracket",
    )

    # V housing: an envelope around the Pi 5 stack, sitting on the rail
    vh = settings.v_housing
    wall = vh.wall_mm * MM
    floor_z = top_z + rail_h
    vlen = (vh.to_x_mm - vh.from_x_mm) * MM
    vcx = (vh.to_x_mm + vh.from_x_mm) / 2 * MM
    shell = Pos(vcx, 0, floor_z) * Box(vlen, vh.width_mm * MM, vh.height_mm * MM, align=BOTTOM)
    shell -= Pos(vcx, 0, floor_z + wall) * Box(
        vlen - 2 * wall, vh.width_mm * MM - 2 * wall, vh.height_mm * MM - 2 * wall, align=BOTTOM
    )
    # a hole in the floor for the module plug, which mates with the socket in the rail
    for part in build.modules.get("V", ()):
        if part.id != "module-plug":
            continue
        for spot in settings.spots():
            if spot.part_id == part.id and spot.module == "V":
                x, y, _ = spot.placement.at
                shell -= Pos(x, y, floor_z - 1e-4) * Box(
                    part.cad.size("length_mm") + 2 * FIT,
                    part.cad.size("width_mm") + 2 * FIT,
                    wall + 2e-4,
                    align=BOTTOM,
                )
    add("v housing", [(shell, vh.material)], vh.material, wall, (0, 0, -1), "V", "v-housing")

    # P holder: a cradle ring with a flange around the Harrier tube's base
    ph = settings.p_holder
    chute = next(p for p in build.modules["P"] if p.id == "fruity-chutes-harrier-40-42")
    px, py, pz = settings.place[chute.id].at
    tube_r = chute.cad.size("diameter_mm") / 2
    inner = tube_r + 0.1 * MM
    # The tube stands on a lip, raised off the rail so the module plug fits under it
    base_z = top_z + rail_h
    ring = Pos(px, py, base_z) * Cylinder(
        inner + ph.wall_mm * MM, pz - base_z + ph.height_mm * MM, align=BOTTOM
    )
    ring += Pos(px, py, base_z) * Cylinder(inner + 6 * MM, 3 * MM, align=BOTTOM)
    ring -= Pos(px, py, pz) * Cylinder(inner, 1.0, align=BOTTOM)
    ring -= Pos(px, py, base_z - 1e-4) * Cylinder(tube_r - 2 * MM, 1.0, align=BOTTOM)
    add(
        "p holder",
        [(ring, ph.material)],
        ph.material,
        min(ph.wall_mm * MM, 3 * MM),
        (0, 0, -1),
        "P",
        "p-mount",
    )

    weighed = []
    for part in parts:
        mass = sum(piece.volume * settings.materials[mat].density for piece, mat in part.pieces)
        weighed.append(PrintedPart(**{**part.__dict__, "mass": mass}))
    return weighed
