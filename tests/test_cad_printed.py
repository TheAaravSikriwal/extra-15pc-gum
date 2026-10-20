"""My own printed parts and the module envelopes: printable, weighed from their geometry, and
lined up with the parts they hold."""

import math
from pathlib import Path

import pytest

from pcs14.catalog import load_catalog
from pcs14.design import load_build

ROOT = Path(__file__).resolve().parents[1]
MM = 0.001


@pytest.fixture(scope="module")
def made():
    from pcs14.cad.frame import build_frame
    from pcs14.cad.printed import build_printed
    from pcs14.cad.settings import load_settings

    build = load_build(ROOT / "design" / "build.yaml", load_catalog(ROOT / "design" / "catalog"))
    settings = load_settings(ROOT / "design" / "cad.yaml")
    frame = build_frame(build.frame)
    return build, settings, frame, {p.name: p for p in build_printed(build, settings, frame)}


def test_every_printed_part_is_there(made):
    _, _, _, printed = made
    assert set(printed) == {
        "leg front left",
        "leg front right",
        "leg back left",
        "leg back right",
        "battery tray",
        "module rail",
        "gps mast",
        "gps cradle",
        "lidar bracket",
        "remote id mount",
        "safety monitor carrier",
        "camera bracket",
        "v housing",
        "p holder",
    }


def test_walls_are_printable_and_each_part_has_a_flat_face_to_print_on(made):
    from pcs14.cad.printed import has_flat_base

    _, settings, _, printed = made
    for part in printed.values():
        assert part.thinnest_wall >= settings.print.min_wall - 1e-9, part.name
        assert has_flat_base(part.solid, part.print_down), part.name


def test_weights_come_from_volume_and_density(made):
    _, settings, _, printed = made
    for part in printed.values():
        expected = sum(
            piece.volume * settings.materials[material].density for piece, material in part.pieces
        )
        assert part.mass == pytest.approx(expected), part.name
    assert 3 <= printed["leg front left"].mass * 1000 <= 15
    assert 35 <= printed["v housing"].mass * 1000 <= 120
    assert printed["module rail"].mass * 1000 <= 30


def test_the_lidar_bracket_holes_line_up_with_the_lidar(made):
    from pcs14.cad.locate import place_point

    build, settings, _, printed = made
    lidar = next(p for p in build.base if p.id == "benewake-tf-luna")
    spot = settings.place[lidar.id]
    for hole in lidar.cad.holes:
        x, y, _ = place_point((hole.x, hole.y, 0), spot)
        assert not printed["lidar bracket"].solid.is_inside((x, y, -0.0015)), (x, y)


def test_the_camera_bracket_standoffs_meet_the_camera_holes(made):
    from pcs14.cad.locate import place_point

    build, settings, _, printed = made
    camera = next(p for p in build.modules["V"] if p.id == "rpi-camera-module-3")
    spot = settings.place[camera.id]
    bottom = camera.cad.size("bottom_mm")
    for hole in camera.cad.holes:
        # the screw hole runs down each standoff's middle, so probe its wall, 1.8 mm off center
        x, y, z = place_point((hole.x + 0.0018, hole.y, -bottom - 0.0005), spot)
        assert printed["camera bracket"].solid.is_inside((x, y, z)), (x, y, z)
        x, y, z = place_point((hole.x, hole.y, -bottom - 0.0005), spot)
        assert not printed["camera bracket"].solid.is_inside((x, y, z)), "no screw hole"


def test_the_tray_covers_the_packs_whole_slide(made):
    from pcs14.cad.parts import pack_layout

    build, settings, _, printed = made
    layout = pack_layout(
        build.pack.cell,
        build.pack.cell_count,
        settings.pack.tray_max_length_mm * MM,
        settings.pack.tray_max_width_mm * MM,
    )
    tray = printed["battery tray"].solid.bounding_box()
    assert tray.size.X >= layout.length + 2 * settings.pack.slide_mm * MM - 1e-9
    assert tray.max.Z == pytest.approx(0, abs=1e-9)  # right under the bottom plate


def test_the_gps_sits_in_a_cradle_and_the_rail_takes_the_modules_locks(made):
    """ARK publishes no holes, so the GPS sits in a cradle with a lip around its 50 mm case;
    each module locks onto the rail with thumb screws into heat-set inserts."""
    _, _, _, printed = made
    cradle = printed["gps cradle"].solid.bounding_box().size
    assert (cradle.X, cradle.Y) == pytest.approx((0.0544, 0.0544), abs=1e-4)
    assert cradle.Z == pytest.approx(0.007, abs=1e-4)  # a 3 mm floor and a 4 mm lip
    # three blind 4 mm holes for the inserts, each with a flat round floor
    floor = math.pi * 0.002**2
    rail = printed["module rail"].solid
    assert len([f for f in rail.faces() if abs(f.area - floor) < 1e-8]) == 3
