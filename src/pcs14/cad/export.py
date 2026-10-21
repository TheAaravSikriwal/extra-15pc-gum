"""What leaves the CAD, all from the same pieces:

- a STEP assembly in meters, which opens in any CAD tool
- a simplified mesh for Gazebo (STL, meters)
- a watertight mesh of the body for the wind tunnel: every solid part fused into one skin,
  without the props (they spin) or the wires
- a GLB for the project site, every part a named node
- a 3MF print file per printed part, in millimeters, as slicers expect

None of these get committed (generated meshes and STEP files stay out of git); they land in
outputs/cad/.
"""

from collections import Counter
from pathlib import Path

from build123d import (
    Align,
    Box,
    Compound,
    Cylinder,
    Mesher,
    Pos,
    Unit,
    export_gltf,
    export_step,
    export_stl,
)

GAZEBO_TOLERANCE = 0.001  # m, a coarse mesh is plenty for physics
CFD_SKIPS = ("prop", "wire")
BOTTOM = (Align.CENTER, Align.CENTER, Align.MIN)


def _compound(pieces, looks: bool = False) -> Compound:
    children = []
    for piece in pieces:
        shape = (piece.look or piece.solid) if looks else piece.solid
        shape.label = piece.name
        children.append(shape)
    return Compound(children=children)  # an assembly, so every part keeps its name


def model_shapes(pieces) -> list:
    """What the pictures and the site's model draw: each piece's look where it has one, named
    for the piece, and its plain solid elsewhere."""
    return list(_compound(pieces, looks=True).children)


def export_step_file(pieces, path: Path) -> Path:
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    export_step(_compound(pieces), path, unit=Unit.M)
    return path


def export_gazebo(pieces, path: Path) -> Path:
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    export_stl(_compound(pieces), path, tolerance=GAZEBO_TOLERANCE, angular_tolerance=0.5)
    return path


def _envelope(piece):
    """What the air sees: the pack as its shrink-wrapped box, a motor as a plain cylinder
    (no screw holes), and a part made of several pieces fused into one. Cells touching along
    a line, or nearly matching holes, otherwise leave edges a closed skin can't have."""
    box = piece.solid.bounding_box()
    center = box.center()
    if piece.kind == "pack":
        return Pos(center.X, center.Y, box.min.Z) * Box(
            box.size.X, box.size.Y, box.size.Z, align=BOTTOM
        )
    if piece.kind == "motor":
        return Pos(center.X, center.Y, box.min.Z) * Cylinder(
            box.size.X / 2, box.size.Z, align=BOTTOM
        )
    solids = piece.solid.solids()
    return solids[0].fuse(*solids[1:]).clean() if len(solids) > 1 else piece.solid


def cfd_body(pieces):
    """Every solid part except the props and wires, as the air sees it, fused into one closed
    skin."""
    shapes = [_envelope(p) for p in pieces if p.kind not in CFD_SKIPS]
    body = shapes[0]
    for shape in shapes[1:]:
        body = body.fuse(shape).clean()
    return body


def is_watertight(shape, tolerance: float = 0.0005) -> bool:
    """True if every edge of the shape's triangle mesh is shared by exactly two triangles."""
    vertices, triangles = shape.tessellate(tolerance, 0.3)
    key = {i: (round(v.X, 9), round(v.Y, 9), round(v.Z, 9)) for i, v in enumerate(vertices)}
    edges = Counter()
    for a, b, c in triangles:
        for u, v in ((a, b), (b, c), (c, a)):
            edges[tuple(sorted((key[u], key[v])))] += 1
    return all(count == 2 for count in edges.values())


def export_cfd(pieces, path: Path) -> Path:
    body = cfd_body(pieces)
    if not is_watertight(body):
        raise ValueError("the fused body isn't watertight, so it isn't ready for the wind tunnel")
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    export_stl(body, path, tolerance=0.0003, angular_tolerance=0.2)
    return path


def export_glb(pieces, path: Path) -> Path:
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    export_gltf(
        _compound(pieces, looks=True), path, unit=Unit.M, binary=True, linear_deflection=0.0005
    )
    return path


def export_print_file(name: str, solid, folder: Path) -> Path:
    folder = Path(folder)
    folder.mkdir(parents=True, exist_ok=True)
    path = folder / f"{name.replace(' ', '-')}.3mf"
    mesher = Mesher(unit=Unit.MM)
    mesher.add_shape(solid.scale(1000))
    mesher.write(str(path))
    return path


def export_print_files(part, folder: Path) -> list[Path]:
    """A 3MF for each printed piece of a printed part. Pieces in another material (like the GPS
    mast's carbon tube) are bought, not printed, so they're left out."""
    printed = [solid for solid, material in part.pieces if material == part.material]
    if len(printed) == 1:
        return [export_print_file(part.name, printed[0], folder)]
    return [
        export_print_file(f"{part.name} {k}", solid, folder)
        for k, solid in enumerate(printed, start=1)
    ]
