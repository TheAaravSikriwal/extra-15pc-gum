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
from dataclasses import dataclass, field, replace

from build123d import Align, Compound, Cylinder, Plane, Pos, Sphere

from pcs14.cad.frame import FrameModel, build_frame
from pcs14.cad.locate import placed
from pcs14.cad.looks import look_for
from pcs14.cad.parts import build_part, pack_layout, pack_solid, prop_disk, prop_look, prop_solid
from pcs14.cad.printed import build_printed
from pcs14.cad.settings import WIRING_PARTS, CadSettings, Wire
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
    # what the pictures and the site's model show, inside the solid; the checks use the solid
    look: object | None = None


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


def _volume(wire: Wire) -> float:
    return wire_length(wire) * wire.diameter**2


def _with_hardware(pieces, build, settings, catalog_parts):
    """Each part's hardware, from the hardware list, on its pieces (split by their weight). The
    budget is the catalog's hardware entry for that module, shared out the same way, so the CAD
    and the sizing model count the same grams."""
    from pcs14.cad import hardware

    held = hardware.by_part(settings)
    if not held:
        return pieces
    module_of = hardware.module_of_parts(build)
    modules = hardware.by_module(settings, module_of)
    owner = {}
    for item in settings.hardware:
        owner[item.holds] = item.module or module_of[item.holds]
    out = []
    for piece in pieces:
        grams = held.get(piece.part_id or "", 0.0)
        if not grams:
            out.append(piece)
            continue
        group = [p for p in pieces if p.part_id == piece.part_id]
        share = (
            piece.mass / sum(p.mass for p in group)
            if sum(p.mass for p in group)
            else 1 / len(group)
        )
        module = owner[piece.part_id]
        entry = catalog_parts.get(hardware.HARDWARE_PARTS[module])
        budget = entry.mass * grams / modules[module] if entry is not None else 0.0
        out.append(
            replace(
                piece,
                mass=piece.mass + grams * share,
                budget_mass=piece.budget_mass + budget * share,
            )
        )
    return out


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
                look=frame.look,
            )
        ]
        motor = build_part(build.motor)
        motor_look = look_for(build.motor)
        blades, look, disk = prop_solid(build.prop), prop_look(build.prop), prop_disk(build.prop)
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
                    look=Pos(x, y, z) * motor_look if motor_look is not None else None,
                )
            )
            pieces.append(
                Piece(
                    f"prop {corner}",
                    Pos(x, y, z + hub_z) * blades,
                    "prop",
                    "base",
                    build.prop.mass,
                    build.prop.mass,
                    part_id=build.prop.id,
                    look=Pos(x, y, z + hub_z) * look,
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
        for spot in settings.spots():
            part = catalog_parts[spot.part_id]
            mass = part.mass * spot.share
            look = look_for(part)
            pieces.append(
                Piece(
                    spot.name,
                    placed(build_part(part), spot.placement),
                    "bought",
                    spot.module or module_of[spot.part_id],
                    mass,
                    mass,
                    moving=spot.part_id in MOVING_PARTS,
                    part_id=spot.part_id,
                    look=placed(look, spot.placement) if look is not None else None,
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

        pieces = _with_hardware(pieces, build, settings, catalog_parts)
        # each module's wiring entry spreads over its routes by volume; a route with a part of
        # its own (the camera's ribbon) weighs that part instead
        own = {"camera cable": catalog_parts.get("rpi-camera-cable-standard-mini")}
        volume = {}
        for wire in settings.wires:
            if own.get(wire.name) is None:
                volume[wire.module] = volume.get(wire.module, 0.0) + _volume(wire)
        for wire in settings.wires:
            tube = wire_tube(wire)
            wiring = catalog_parts.get(WIRING_PARTS[wire.module])
            if own.get(wire.name) is not None:
                mass = own[wire.name].mass
            elif wiring is not None:
                mass = wiring.mass * _volume(wire) / volume[wire.module]
            else:
                mass = 0.0
            pieces.append(
                Piece(f"wire {wire.name}", tube, "wire", wire.module, mass, mass, moving=True)
            )
        return pieces, disks

    def build_part_mass(self, part_id: str) -> float:
        """One catalog part's mass, however many spots it's split across."""
        parts = [self.build.esc, *self.build.base, *self.build.all_module_parts()]
        return next(p.mass for p in parts if p.id == part_id)

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
