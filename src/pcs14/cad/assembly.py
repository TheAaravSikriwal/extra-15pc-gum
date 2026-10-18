"""The assembly: every part of the drone placed, for any module combination.

Drone builds every piece once (the frame, motors, props, the pack, the bought parts at their
spots in design/cad.yaml, the printed parts, and the wire routes as tubes). combination()
then picks the pieces for a set of modules, with the pack slid to a trim position, which
is what the checks step through.

Each piece carries two weights: `mass`, the CAD's best number (printed parts weighed from
their geometry), and `budget_mass`, what the sizing model counts for it today (the catalog's
number, or nothing for a part the catalog doesn't have yet).
"""

import math
from dataclasses import dataclass, field

from build123d import Align, Compound, Cylinder, Plane, Pos, Sphere

from pcs14.cad.frame import FrameModel, build_frame
from pcs14.cad.locate import placed
from pcs14.cad.parts import build_part, pack_layout, pack_solid, prop_disk, prop_look
from pcs14.cad.printed import build_printed
from pcs14.cad.settings import CadSettings, Wire
from pcs14.design import Build

MM = 0.001
BOTTOM = (Align.CENTER, Align.CENTER, Align.MIN)
MOVING_PARTS = {"halow-antenna-915"}  # flexible, so they get the moving-part clearance


@dataclass(frozen=True)
class Piece:
    name: str
    solid: object  # a build123d shape
    kind: str  # frame, motor, prop, pack, bought, printed or wire
    module: str  # base, V, P or C
    mass: float  # kg, the CAD's best number
    budget_mass: float  # kg, what the sizing model counts for it today
    moving: bool = False
    part_id: str | None = None


@dataclass(frozen=True)
class Assembly:
    modules: frozenset[str]
    pieces: tuple[Piece, ...]
    prop_disks: tuple  # the disks the props sweep, for the clearance checks
    pack_x: float  # m, where the pack's center sits along x
    frame: FrameModel
    wire_lengths: dict[str, float] = field(default_factory=dict)  # m, every wire in the build

    def piece(self, name: str) -> Piece:
        return next(p for p in self.pieces if p.name == name)


def _corner(x: float, y: float) -> str:
    return f"{'front' if x > 0 else 'back'} {'left' if y > 0 else 'right'}"


def wire_tube(wire: Wire):
    """A wire's route as a tube: a cylinder per straight run and a ball at each bend."""
    radius = wire.diameter / 2
    pieces = []
    points = wire.path
    for a, b in zip(points, points[1:], strict=False):
        length = math.dist(a, b)
        if length <= 0:
            continue
        direction = tuple(bi - ai for ai, bi in zip(a, b, strict=True))
        plane = Plane(origin=a, z_dir=direction)
        pieces.append(plane.location * Cylinder(radius, length, align=BOTTOM))
    for point in points[1:-1]:
        pieces.append(Pos(*point) * Sphere(radius))
    tube = Compound(pieces)
    tube.label = f"wire {wire.name}"
    return tube


def wire_length(wire: Wire) -> float:
    return sum(math.dist(a, b) for a, b in zip(wire.path, wire.path[1:], strict=False))


class Drone:
    """Every piece of the build, ready to be combined."""

    def __init__(self, build: Build, settings: CadSettings):
        self.build, self.settings = build, settings
        self.frame = build_frame(build.frame)
        pack = settings.pack
        self.layout = pack_layout(
            build.pack.cell,
            build.pack.cell_count,
            pack.tray_max_length_mm * MM,
            pack.tray_max_width_mm * MM,
        )
        self.home_x = pack.x_mm * MM
        tray_t = pack.tray_thickness_mm * MM
        self._pack_shape = Pos(0, 0, -tray_t - self.layout.height) * pack_solid(
            build.pack.cell, self.layout
        )
        self._pieces, self._disks = self._build_pieces()

    def _build_pieces(self):
        build, settings, frame = self.build, self.settings, self.frame
        pieces = [
            Piece(
                "frame",
                frame.solid,
                "frame",
                "base",
                build.frame.mass,
                build.frame.mass,
                part_id=build.frame.id,
            )
        ]
        motor = build_part(build.motor)
        look, disk = prop_look(build.prop), prop_disk(build.prop)
        hub_z = build.motor.cad.size("bell_length_mm") + 0.002  # props sit on the shaft
        disks = []
        for x, y, z in frame.motor_mounts:
            corner = _corner(x, y)
            pieces.append(
                Piece(
                    f"motor {corner}",
                    Pos(x, y, z) * motor,
                    "motor",
                    "base",
                    build.motor.mass,
                    build.motor.mass,
                    part_id=build.motor.id,
                )
            )
            pieces.append(
                Piece(
                    f"prop {corner}",
                    Pos(x, y, z + hub_z) * look,
                    "prop",
                    "base",
                    build.prop.mass,
                    build.prop.mass,
                    part_id=build.prop.id,
                )
            )
            disks.append(Pos(x, y, z + hub_z) * disk)

        module_of = {part.id: "base" for part in build.base}
        for module, parts in build.modules.items():
            module_of.update({part.id: module for part in parts})
        catalog_parts = {
            part.id: part
            for part in [
                build.esc,
                *build.base,
                *[p for parts in build.modules.values() for p in parts],
            ]
        }
        module_of[build.esc.id] = "base"
        for part_id, spot in settings.place.items():
            part = catalog_parts[part_id]
            pieces.append(
                Piece(
                    part_id,
                    placed(build_part(part), spot),
                    "bought",
                    module_of[part_id],
                    part.mass,
                    part.mass,
                    moving=part_id in MOVING_PARTS,
                    part_id=part_id,
                )
            )

        budget = {part_id: part.mass for part_id, part in catalog_parts.items()}
        printed = build_printed(build, settings, frame)
        sharing = {}
        for part in printed:
            sharing.setdefault(part.catalog_id, []).append(part)
        for part in printed:
            group = sharing[part.catalog_id]
            share = budget.get(part.catalog_id, 0.0) * part.mass / sum(p.mass for p in group)
            pieces.append(
                Piece(
                    part.name,
                    part.solid,
                    "printed",
                    part.module,
                    part.mass,
                    share,
                    part_id=part.catalog_id,
                )
            )

        wiring = {"base": catalog_parts.get("base-wiring"), "V": None, "P": None, "C": None}
        base_wires = [w for w in settings.wires if w.module == "base"]
        base_volume = sum(wire_length(w) * w.diameter**2 for w in base_wires)
        for wire in settings.wires:
            tube = wire_tube(wire)
            if wire.module == "base" and wiring["base"] is not None:
                mass = wiring["base"].mass * wire_length(wire) * wire.diameter**2 / base_volume
            elif wire.name == "camera cable" and "rpi-camera-cable-standard-mini" in catalog_parts:
                mass = catalog_parts["rpi-camera-cable-standard-mini"].mass
            else:
                mass = 0.0
            pieces.append(
                Piece(f"wire {wire.name}", tube, "wire", wire.module, mass, mass, moving=True)
            )
        return pieces, disks

    def combination(self, modules, pack_x: float | None = None) -> Assembly:
        modules = frozenset(modules)
        x = self.home_x if pack_x is None else pack_x
        pack = self.build.pack
        chosen = [p for p in self._pieces if p.module == "base" or p.module in modules]
        chosen.append(
            Piece(
                "pack",
                Pos(x, 0, 0) * self._pack_shape,
                "pack",
                "base",
                pack.mass,
                pack.mass,
                part_id=pack.cell.id,
            )
        )
        lengths = {wire.name: wire_length(wire) for wire in self.settings.wires}
        return Assembly(modules, tuple(chosen), tuple(self._disks), x, self.frame, lengths)


def floating(assembly: Assembly, tolerance: float = 0.0002) -> list[str]:
    """Pieces that touch nothing: every part should rest on, or bolt to, something."""
    pieces = [p for p in assembly.pieces if p.kind != "wire"]
    boxes = {p.name: p.solid.bounding_box() for p in pieces}
    alone = []
    for piece in pieces:
        box = boxes[piece.name]
        touching = False
        for other in pieces:
            if other is piece:
                continue
            near = boxes[other.name]
            if (
                near.min.X > box.max.X + tolerance
                or near.max.X < box.min.X - tolerance
                or near.min.Y > box.max.Y + tolerance
                or near.max.Y < box.min.Y - tolerance
                or near.min.Z > box.max.Z + tolerance
                or near.max.Z < box.min.Z - tolerance
            ):
                continue
            if piece.solid.distance_to(other.solid) <= tolerance:
                touching = True
                break
        if not touching:
            alone.append(piece.name)
    return alone
