"""What leaves the CAD: STEP, the Gazebo and CFD meshes, the GLB for the site, print files,
and stills in the project's look. Tested on small made-up pieces, so it stays quick."""

import struct

import pytest

MM = 0.001


def pieces():
    from build123d import Box, Cylinder, Pos

    from pcs14.cad.assembly import Piece

    return [
        Piece("frame", Box(0.30, 0.03, 0.035), "frame", "base", 0.3, 0.3),
        Piece("pack", Pos(0.0, 0, -0.035) * Box(0.14, 0.065, 0.043), "pack", "base", 0.8, 0.8),
        Piece("v housing", Pos(0, 0, 0.05) * Box(0.06, 0.09, 0.07), "printed", "V", 0.04, 0.05),
        Piece(
            "prop front left", Pos(0.1, 0, 0.03) * Cylinder(0.05, 0.009), "prop", "base", 0.02, 0.02
        ),
    ]


def test_the_step_reads_back_with_the_same_volume(tmp_path):
    from build123d import import_step

    from pcs14.cad.export import export_step_file

    path = export_step_file(pieces(), tmp_path / "drone.step")
    back = import_step(path)  # comes back in millimeters
    total = sum(p.solid.volume for p in pieces())
    assert back.volume * 1e-9 == pytest.approx(total, rel=1e-4)


def test_the_cfd_mesh_is_one_watertight_skin_without_the_props(tmp_path):
    from pcs14.cad.export import cfd_body, is_watertight

    body = cfd_body(pieces())
    assert is_watertight(body)
    assert body.bounding_box().max.X < 0.151  # the prop at x = 0.1 + 0.05 isn't in it


def test_the_glb_names_every_part(tmp_path):
    from pygltflib import GLTF2

    from pcs14.cad.export import export_glb

    path = export_glb(pieces(), tmp_path / "drone.glb")
    names = {node.name for node in GLTF2().load(str(path)).nodes if node.name}
    assert {"frame", "pack", "v housing", "prop front left"} <= names


def test_print_files_come_out_in_millimeters(tmp_path):
    from build123d import Mesher

    from pcs14.cad.export import export_print_file

    v_housing = pieces()[2]
    path = export_print_file(v_housing.name, v_housing.solid, tmp_path)
    meshes = Mesher().read(str(path))
    size = meshes[0].bounding_box().size
    assert sorted([size.X, size.Y, size.Z]) == pytest.approx(sorted([60, 90, 70]), abs=0.01)


def test_the_stills_come_out_at_the_post_size(tmp_path):
    from pcs14.cad.views import render_stills

    paths = render_stills(pieces(), tmp_path, title="A made-up drone")
    assert sorted(p.stem for p in paths) == ["exploded", "front", "side", "three-quarter", "top"]
    for path in paths:
        width, height = struct.unpack(">II", path.read_bytes()[16:24])
        assert (width, height) == (1080, 1350), path.name


def test_only_the_printed_pieces_of_a_part_get_print_files(tmp_path):
    from build123d import Box, Cylinder, Pos

    from pcs14.cad.export import export_print_files
    from pcs14.cad.printed import PrintedPart

    mast = PrintedPart(
        name="gps mast",
        pieces=(
            (Box(0.014, 0.014, 0.008), "tpu"),
            (Pos(0, 0, 0.1) * Box(0.024, 0.024, 0.003), "tpu"),
            (Pos(0, 0, 0.05) * Cylinder(0.004, 0.09), "carbon"),  # a bought tube, not printed
        ),
        material="tpu",
        thinnest_wall=0.003,
        print_down=(0, 0, -1),
        module="V",
        catalog_id="gps-mast",
    )
    paths = export_print_files(mast, tmp_path)
    assert [p.name for p in paths] == ["gps-mast-1.3mf", "gps-mast-2.3mf"]


def test_the_cfd_body_wraps_the_pack_like_heat_shrink():
    from build123d import Box, Compound, Cylinder, Pos, Rot

    from pcs14.cad.assembly import Piece
    from pcs14.cad.export import cfd_body, is_watertight

    radius, length = 0.01085, 0.0702
    cell = Rot(0, 90, 0) * Cylinder(radius, length)
    cells = Compound([Pos(0, -radius, -0.011) * cell, Pos(0, radius, -0.011) * cell])
    frame = Box(0.3, 0.03, 0.003)
    parts = [
        Piece("frame", frame, "frame", "base", 0.3, 0.3),
        Piece("pack", Pos(0, 0, -0.0015) * cells, "pack", "base", 0.14, 0.14),
    ]
    body = cfd_body(parts)
    assert is_watertight(body)
    wrapped = length * (4 * radius) * (2 * radius)  # the two cells' bounding box
    assert body.volume == pytest.approx(frame.volume + wrapped, rel=1e-6)
