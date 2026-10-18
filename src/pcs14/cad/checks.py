"""The CAD checks, run on each module combination with the pack slid to its best trim:

- collisions: no two solid parts overlap (touching is fine; wires are routes, so they're left out)
- prop clearance: rigid parts 10 mm from the prop disks, moving parts (wires, antennas) 20 mm,
  and the props clear of each other
- parachute cone: nothing in the cone above the chute's mouth
- module rail: everything on the rail fits on it
- balance: in a hover, no motor works more than 5% harder than the average
- compass distance and Remote ID distance: the makers' placement rules
- lidar: its view straight down is clear, and how high it sits when landed (it can't read
  under 20 cm)

The limits come from design/cad.yaml.
"""

import math
from dataclasses import dataclass

from build123d import Align, Cone, Cylinder, Pos

from pcs14.cad.assembly import Assembly, Drone
from pcs14.cad.mass import MassProperties, mass_properties

MM = 0.001
OVERLAP = 1e-9  # m³: anything under 1 mm³ is touching, not colliding
POWER_PARTS = (
    "holybro-tekko32-f4-50a",
    "matek-bec12s-pro",
    "pack",
    "wire battery leads",
    "wire bec feed",
)
LIDAR_BLIND = 0.20  # m, the TF-Luna can't measure closer than this


@dataclass(frozen=True)
class Finding:
    check: str
    passed: bool
    value: float | None  # what was measured (m, m³ or a share)
    limit: float | None
    detail: str
    parts: tuple[str, ...] = ()


@dataclass(frozen=True)
class CombinationResult:
    setup: str
    modules: frozenset[str]
    trim_x: float  # m, where the pack ended up
    overload: float  # the busiest motor's extra share in a hover
    mass: MassProperties
    findings: tuple[Finding, ...]

    @property
    def passed(self) -> bool:
        return all(f.passed for f in self.findings)


def motor_overload(center, half: float) -> float:
    """How much harder the busiest motor works than the average in a hover, with the motors at
    (±half, ±half) and the weight's center at `center`."""
    x, y, _ = center
    return (abs(x) + abs(y)) / half


def best_trim(cg_x: float, mass: float, pack_mass: float, home: float, slide: float) -> float:
    """Where to slide the pack to bring the center of gravity over x = 0, within its range."""
    wanted = home - cg_x * mass / pack_mass
    return min(max(wanted, home - slide), home + slide)


def _near(a, b, gap: float) -> bool:
    return not (
        b.min.X > a.max.X + gap
        or b.max.X < a.min.X - gap
        or b.min.Y > a.max.Y + gap
        or b.max.Y < a.min.Y - gap
        or b.min.Z > a.max.Z + gap
        or b.max.Z < a.min.Z - gap
    )


def _overlap(a, b) -> float:
    """The volume two shapes share. Surfaces that don't touch can still mean one shape sits
    entirely inside the other, so that gets checked before giving up."""
    if a.distance_to(b) > 0:
        inside = a.is_inside(b.vertices()[0].center()) or b.is_inside(a.vertices()[0].center())
        if not inside:
            return 0.0
    common = a & b
    return common.volume if common is not None else 0.0


def collisions(pieces) -> list[Finding]:
    solid = [p for p in pieces if p.kind != "wire"]
    boxes = [p.solid.bounding_box() for p in solid]
    found = []
    for i, a in enumerate(solid):
        for j in range(i + 1, len(solid)):
            b = solid[j]
            if not _near(boxes[i], boxes[j], 0):
                continue
            volume = _overlap(a.solid, b.solid)
            if volume > OVERLAP:
                found.append(
                    Finding(
                        "collisions",
                        False,
                        volume,
                        OVERLAP,
                        f"{a.name} and {b.name} overlap by {volume * 1e9:.0f} mm³",
                        (a.name, b.name),
                    )
                )
    return found


def prop_clearances(disks, pieces, rigid: float, moving: float) -> list[Finding]:
    found = []
    for k, disk in enumerate(disks):
        box = disk.bounding_box()
        for piece in pieces:
            if piece.kind in ("motor", "prop"):
                continue
            limit = moving if piece.moving else rigid
            if not _near(box, piece.solid.bounding_box(), limit + 0.005):
                continue
            gap = disk.distance_to(piece.solid)
            found.append(
                Finding(
                    "prop clearance",
                    gap >= limit,
                    gap,
                    limit,
                    f"{piece.name} is {gap / MM:.1f} mm from prop {k + 1}'s disk "
                    f"(needs {limit / MM:.0f})",
                    (f"prop disk {k + 1}", piece.name),
                )
            )
    for i in range(len(disks)):
        for j in range(i + 1, len(disks)):
            gap = disks[i].distance_to(disks[j])
            found.append(
                Finding(
                    "prop clearance",
                    gap >= rigid,
                    gap,
                    rigid,
                    f"props {i + 1} and {j + 1} are {gap / MM:.1f} mm apart",
                    (f"prop disk {i + 1}", f"prop disk {j + 1}"),
                )
            )
    return found


def in_chute_cone(pieces, mouth, mouth_radius: float, half_angle_deg: float, height: float):
    """Names of the pieces inside the cone the chute opens through."""
    top = mouth_radius + height * math.tan(math.radians(half_angle_deg))
    cone = Pos(*mouth) * Cone(
        mouth_radius, top, height, align=(Align.CENTER, Align.CENTER, Align.MIN)
    )
    box = cone.bounding_box()
    return [
        p.name
        for p in pieces
        if _near(box, p.solid.bounding_box(), 0) and _overlap(cone, p.solid) > OVERLAP
    ]


def _pack_clear(assembly: Assembly) -> bool:
    pack = assembly.piece("pack")
    box = pack.solid.bounding_box()
    for other in assembly.pieces:
        if other is pack or other.kind == "wire":
            continue
        if (
            _near(box, other.solid.bounding_box(), 0)
            and _overlap(pack.solid, other.solid) > OVERLAP
        ):
            return False
    return True


def trim(drone: Drone, modules) -> Assembly:
    """The pack slid to where it balances the drone best without hitting anything."""
    home = drone.combination(modules)
    props = mass_properties(home.pieces)
    pack_mass = home.piece("pack").mass
    slide = drone.settings.pack.slide_mm * MM
    ideal = best_trim(props.center[0], props.mass, pack_mass, home.pack_x, slide)
    steps = range(-round(slide / MM), round(slide / MM) + 1)
    candidates = sorted((home.pack_x + k * MM for k in steps), key=lambda x: abs(x - ideal))
    for x in candidates:
        assembly = drone.combination(modules, pack_x=x)
        if _pack_clear(assembly):
            return assembly
    return drone.combination(modules, pack_x=ideal)


def check_combination(drone: Drone, setup: str, modules) -> CombinationResult:
    settings, checks = drone.settings, drone.settings.checks
    assembly = trim(drone, modules)
    props = mass_properties(assembly.pieces)
    half = drone.build.frame.wheelbase / 2 / math.sqrt(2)
    overload = motor_overload(props.center, half)
    findings = [
        Finding(
            "balance",
            overload <= checks.max_motor_overload,
            overload,
            checks.max_motor_overload,
            f"with the pack at x = {assembly.pack_x / MM:.0f} mm, the center of gravity sits "
            f"{props.center[0] / MM:+.1f} mm along x and {props.center[1] / MM:+.1f} mm along y, "
            f"so the busiest motor works {overload * 100:.1f}% harder",
        )
    ]
    hits = collisions(assembly.pieces)
    findings += hits or [Finding("collisions", True, 0.0, OVERLAP, "nothing overlaps")]
    findings += prop_clearances(
        assembly.prop_disks, assembly.pieces, checks.rigid_clearance, checks.moving_clearance
    )

    names = {p.name for p in assembly.pieces}
    chute_id = "fruity-chutes-harrier-40-42"
    if chute_id in names:
        chute = next(p for p in drone.build.modules["P"] if p.id == chute_id)
        x, y, z = settings.place[chute_id].at
        mouth = (x, y, z + chute.cad.size("length_mm"))
        others = [p for p in assembly.pieces if p.name != chute_id]
        blocked = in_chute_cone(
            others,
            mouth,
            chute.cad.size("diameter_mm") / 2,
            checks.chute_cone_half_angle_deg,
            checks.chute_cone_height,
        )
        findings.append(
            Finding(
                "parachute cone",
                not blocked,
                float(len(blocked)),
                0.0,
                "nothing in the chute's way"
                if not blocked
                else "in the way: " + ", ".join(blocked),
                tuple(blocked),
            )
        )

    rail = settings.rail
    for name in ("v housing", "p holder"):
        if name in names:
            box = assembly.piece(name).solid.bounding_box()
            fits = box.min.X >= rail.from_x_mm * MM - 1e-6 and box.max.X <= rail.to_x_mm * MM + 1e-6
            findings.append(
                Finding(
                    "module rail",
                    fits,
                    None,
                    None,
                    f"{name} spans x = {box.min.X / MM:.0f} to {box.max.X / MM:.0f} mm, on a "
                    f"rail from {rail.from_x_mm:.0f} to {rail.to_x_mm:.0f}",
                    (name,),
                )
            )

    gps_id, rid_id = "matek-m10q-5883", "ruko-r111"
    if gps_id in names:
        gps = assembly.piece(gps_id).solid
        power = [
            p for p in assembly.pieces if p.name in POWER_PARTS or p.name.startswith("wire motor")
        ]
        power += [p for p in assembly.pieces if p.kind == "motor"]
        nearest = min(power, key=lambda p: gps.distance_to(p.solid))
        gap = gps.distance_to(nearest.solid)
        findings.append(
            Finding(
                "compass distance",
                gap >= checks.compass_from_power,
                gap,
                checks.compass_from_power,
                f"the compass is {gap / MM:.0f} mm from {nearest.name} (Matek asks for 100)",
                (gps_id, nearest.name),
            )
        )
        if rid_id in names:
            gap = gps.distance_to(assembly.piece(rid_id).solid)
            findings.append(
                Finding(
                    "remote id distance",
                    gap >= checks.remote_id_from_gps,
                    gap,
                    checks.remote_id_from_gps,
                    f"the Remote ID module is {gap / MM:.0f} mm from the GPS",
                    (rid_id, gps_id),
                )
            )

    lidar_id = "benewake-tf-luna"
    if lidar_id in names:
        lidar = assembly.piece(lidar_id).solid.bounding_box()
        ground = min(
            p.solid.bounding_box().min.Z for p in assembly.pieces if p.name.startswith("leg")
        )
        height = lidar.min.Z - ground
        column = Pos(lidar.center().X, lidar.center().Y, ground) * Cylinder(
            0.008, height, align=(Align.CENTER, Align.CENTER, Align.MIN)
        )
        blockers = [
            p.name
            for p in assembly.pieces
            if p.name != lidar_id
            and p.kind != "wire"
            and _near(column.bounding_box(), p.solid.bounding_box(), 0)
            and _overlap(column, p.solid) > OVERLAP
        ]
        findings.append(
            Finding(
                "lidar view",
                not blockers,
                height,
                None,
                (
                    f"the lidar sits {height / MM:.0f} mm off the ground when landed, so it can't "
                    f"read the last {max(0.0, LIDAR_BLIND - height) / MM:.0f} mm of a landing"
                )
                + ("" if not blockers else "; in its way: " + ", ".join(blockers)),
                tuple(blockers),
            )
        )
    return CombinationResult(
        setup, frozenset(modules), assembly.pack_x, overload, props, tuple(findings)
    )
