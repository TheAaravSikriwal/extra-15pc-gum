"""Builders for bought parts: each cad block becomes a solid with the catalog's dimensions.
Everything inside is in meters, so 35 mm is 0.035."""

from pathlib import Path

import pytest

from pcs14.catalog import load_catalog

ROOT = Path(__file__).resolve().parents[1]
MM = 0.001


@pytest.fixture(scope="module")
def catalog():
    return load_catalog(ROOT / "design" / "catalog")


def size(shape):
    box = shape.bounding_box()
    return (box.size.X / MM, box.size.Y / MM, box.size.Z / MM)


def inside(shape, x_mm, y_mm, z_mm):
    return shape.is_inside((x_mm * MM, y_mm * MM, z_mm * MM))


def test_a_board_has_its_size_and_its_holes(catalog):
    from pcs14.cad.parts import build_part

    fc = build_part(catalog.component("holybro-kakute-h7"))
    assert size(fc) == pytest.approx((35, 35, 1.8 + 1.6 + 4.0))
    assert not inside(fc, 15.25, 15.25, 0.8)  # a mounting hole
    assert inside(fc, 10, 10, 0.8)  # solid board next to it


def test_a_box_and_a_cylinder(catalog):
    from pcs14.cad.parts import build_part

    assert size(build_part(catalog.component("radiomaster-rp2-v2"))) == pytest.approx((13, 11, 7))
    chute = build_part(catalog.component("fruity-chutes-harrier-40-42"))
    assert size(chute) == pytest.approx((40, 40, 154))


def test_the_motor_mounts_on_its_19_mm_pattern(catalog):
    from pcs14.cad.parts import build_part

    motor = build_part(catalog.motor("emax-e3-2814-850kv"))
    assert size(motor) == pytest.approx((35.1, 35.1, 45.5))
    assert not inside(motor, 9.5, 9.5, 1)  # a screw hole in the base
    assert inside(motor, 0, 0, 40)  # the shaft, above the bell
    assert not inside(motor, 5, 0, 40)  # but only 5 mm across


def test_the_prop_disk_and_its_look(catalog):
    from pcs14.cad.parts import prop_disk, prop_look

    prop = catalog.prop("gemfan-1050x3")
    disk = prop_disk(prop)
    assert size(disk) == pytest.approx((254, 254, 9))
    look = prop_look(prop)
    assert not inside(look, 0, 0, 4.5)  # the 5 mm bore
    for got, limit in zip(size(look), size(disk), strict=True):
        assert got <= limit + 1e-6  # the blades stay inside the disk the checks use


def test_a_cell(catalog):
    from pcs14.cad.parts import build_part

    assert size(build_part(catalog.cell("molicel-p42a"))) == pytest.approx((21.7, 21.7, 70.2))


@pytest.mark.parametrize(
    ("max_length", "max_width", "layout", "dims"),
    [
        # a roomy tray: two cells deep, six across, one layer, the flattest pack
        (150, 150, (2, 6, 1), (2 * 70.2, 6 * 21.7, 21.7)),
        # a narrow tray: two deep, three across, two layers
        (150, 90, (2, 3, 2), (2 * 70.2, 3 * 21.7, 2 * 21.7)),
    ],
)
def test_the_pack_picks_the_flattest_layout_that_fits(catalog, max_length, max_width, layout, dims):
    from pcs14.cad.parts import pack_layout

    cell = catalog.cell("molicel-p42a")
    picked = pack_layout(cell, cells=12, max_length=max_length * MM, max_width=max_width * MM)
    assert (picked.along, picked.across, picked.layers) == layout
    assert (picked.length / MM, picked.width / MM, picked.height / MM) == pytest.approx(dims)


def test_the_pack_solid_holds_every_cell(catalog):
    from pcs14.cad.parts import pack_layout, pack_solid

    cell = catalog.cell("molicel-p42a")
    layout = pack_layout(cell, cells=12, max_length=0.150, max_width=0.090)
    pack = pack_solid(cell, layout)
    assert len(pack.solids()) == 12
    assert size(pack) == pytest.approx((140.4, 65.1, 43.4))
