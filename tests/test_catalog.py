"""The parts catalog: every file has to match its format, and every number needs a source."""

import shutil
from pathlib import Path

import pytest

from pcs14.catalog import CatalogError, SourceKind, load_catalog

FIXTURES = Path(__file__).parent / "fixtures" / "catalog"


@pytest.fixture
def catalog():
    return load_catalog(FIXTURES, allow_made_up=True)


@pytest.fixture
def scratch(tmp_path):
    """A copy of the made-up catalog that a test can break."""
    copy = tmp_path / "catalog"
    shutil.copytree(FIXTURES, copy)
    return copy


def write(folder: Path, name: str, text: str) -> None:
    (folder / name).write_text(text, encoding="utf-8")


GOOD_PROP = """type: prop
id: testco-p9x5
maker: Testco
model: P9x5
source: {kind: made_up, note: test}
mass_g: 12
diameter_in: 9
pitch_in: 5
blades: 2
"""


def test_the_made_up_catalog_loads(catalog):
    assert len(catalog.motors) == 1
    assert len(catalog.props) == 1
    assert len(catalog.cells) == 1
    assert len(catalog.escs) == 1
    assert len(catalog.frames) == 1
    assert len(catalog.components) == 14


def test_every_test_part_is_labeled_made_up(catalog):
    for part in catalog.all_parts():
        assert part.source.kind is SourceKind.MADE_UP, part.id


def test_made_up_parts_cant_get_into_the_real_catalog():
    with pytest.raises(CatalogError, match="made up"):
        load_catalog(FIXTURES)


def test_numbers_come_out_metric(catalog):
    motor = catalog.motor("testco-m2810-900kv")
    prop = catalog.prop("testco-p10x45")
    cell = catalog.cell("testco-c21700-45")
    frame = catalog.frame("testco-x10")
    assert motor.mass == pytest.approx(0.070)
    assert prop.diameter == pytest.approx(0.254)
    assert prop.pitch == pytest.approx(0.1143)
    assert prop.disk_area == pytest.approx(0.0506707, rel=1e-5)  # pi * 0.127^2
    assert cell.capacity == pytest.approx(16200)  # coulombs
    assert cell.internal_resistance == pytest.approx(0.015)
    assert frame.drag_area == pytest.approx(0.015)
    row = motor.thrust_tables[0].rows[-1]
    assert row.thrust == pytest.approx(2.1 * 9.80665)
    assert row.power == pytest.approx(24.0 * 26.5)  # volts times amps, when no power column


def test_unknown_part_lists_what_is_there(catalog):
    with pytest.raises(CatalogError, match="testco-m2810-900kv"):
        catalog.motor("nope")


def test_a_good_new_file_loads(scratch):
    write(scratch / "props", "testco-p9x5.yaml", GOOD_PROP)
    assert "testco-p9x5" in load_catalog(scratch, allow_made_up=True).props


def test_missing_source_fails(scratch):
    write(
        scratch / "props",
        "bad.yaml",
        GOOD_PROP.replace("source: {kind: made_up, note: test}\n", ""),
    )
    with pytest.raises(CatalogError, match="bad.yaml.*source"):
        load_catalog(scratch, allow_made_up=True)


def test_manufacturer_numbers_need_a_link(scratch):
    write(
        scratch / "props",
        "bad.yaml",
        GOOD_PROP.replace("kind: made_up, note: test", "kind: manufacturer"),
    )
    with pytest.raises(CatalogError, match="link"):
        load_catalog(scratch, allow_made_up=True)


def test_estimates_need_a_note_saying_how(scratch):
    write(
        scratch / "props",
        "bad.yaml",
        GOOD_PROP.replace("kind: made_up, note: test", "kind: estimate"),
    )
    with pytest.raises(CatalogError, match="note"):
        load_catalog(scratch, allow_made_up=True)


def test_a_number_without_its_unit_says_which_field_was_meant(scratch):
    write(scratch / "props", "bad.yaml", GOOD_PROP.replace("mass_g: 12", "mass: 12"))
    with pytest.raises(CatalogError, match="mass_g"):
        load_catalog(scratch, allow_made_up=True)


def test_a_typo_fails(scratch):
    write(scratch / "props", "bad.yaml", GOOD_PROP.replace("blades: 2", "blaeds: 2"))
    with pytest.raises(CatalogError, match="blaeds"):
        load_catalog(scratch, allow_made_up=True)


def test_a_part_in_the_wrong_folder_fails(scratch):
    write(scratch / "motors", "testco-p9x5.yaml", GOOD_PROP)
    with pytest.raises(CatalogError, match="prop.*motors"):
        load_catalog(scratch, allow_made_up=True)


def test_two_parts_cant_share_an_id(scratch):
    write(scratch / "props", "copy.yaml", GOOD_PROP.replace("testco-p9x5", "testco-p10x45"))
    with pytest.raises(CatalogError, match="testco-p10x45"):
        load_catalog(scratch, allow_made_up=True)


def test_a_thrust_table_has_to_name_a_real_prop(scratch):
    motor = scratch / "motors" / "testco-m2810-900kv.yaml"
    motor.write_text(motor.read_text().replace("prop: testco-p10x45", "prop: testco-p99"), "utf-8")
    with pytest.raises(CatalogError, match="testco-p99"):
        load_catalog(scratch, allow_made_up=True)


def test_thrust_has_to_rise_with_throttle(scratch):
    motor = scratch / "motors" / "testco-m2810-900kv.yaml"
    motor.write_text(motor.read_text().replace("thrust_g: 900,", "thrust_g: 500,"), "utf-8")
    with pytest.raises(CatalogError, match="rise"):
        load_catalog(scratch, allow_made_up=True)


def test_a_cell_curve_has_to_run_from_empty_to_full(scratch):
    cell = scratch / "cells" / "testco-c21700-45.yaml"
    cell.write_text(cell.read_text().replace("  - {soc: 1.00, voltage_v: 4.18}\n", ""), "utf-8")
    with pytest.raises(CatalogError, match="full"):
        load_catalog(scratch, allow_made_up=True)


def test_power_draw_needs_a_source(scratch):
    write(
        scratch / "components",
        "bad.yaml",
        "type: component\nid: testco-x\nmaker: Testco\nmodel: x\n"
        "source: {kind: made_up, note: test}\nmass_g: 5\npower_w: 3\n",
    )
    with pytest.raises(CatalogError, match="power_source"):
        load_catalog(scratch, allow_made_up=True)
