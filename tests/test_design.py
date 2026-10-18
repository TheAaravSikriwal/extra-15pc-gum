"""The targets and the build file, loaded as objects."""

import shutil
from pathlib import Path

import pytest

from pcs14.catalog import CatalogError, load_catalog
from pcs14.design import DesignError, load_build, load_targets

ROOT = Path(__file__).resolve().parents[1]
FIXTURES = Path(__file__).parent / "fixtures"
TARGETS = ROOT / "design" / "targets.yaml"


def test_targets_come_out_metric(targets):
    assert targets.reserve_fraction == 0.20
    assert targets.cruise_speed == 10
    assert targets.sizing_case == "mission"
    assert targets.growth_margin == pytest.approx(0.200)
    assert targets.min_thrust_to_weight == 2.0
    mission = targets.setups["mission"]
    assert mission.min_hover_time == pytest.approx(21 * 60)
    assert mission.min_top_speed == pytest.approx(80 / 3.6)
    assert targets.setups["max"].max_takeoff_weight == pytest.approx(2.5)


def test_there_are_eight_module_combinations(targets):
    combos = {c.name: c for c in targets.combinations()}
    assert list(combos) == ["base", "V", "P", "C", "mission", "V+C", "P+C", "max"]
    assert combos["mission"].modules == frozenset("VP")
    assert combos["max"].modules == frozenset("VPC")


def test_unnamed_combinations_borrow_from_the_smallest_setup_that_holds_them(targets):
    combos = {c.name: c for c in targets.combinations()}
    assert combos["V"].min_hover_time == combos["mission"].min_hover_time
    assert combos["V"].min_top_speed == combos["mission"].min_top_speed
    assert combos["V"].required
    assert combos["C"].min_hover_time == combos["max"].min_hover_time
    assert combos["C"].payload == pytest.approx(0.250)
    assert not combos["C"].required
    assert not combos["P+C"].required


def test_the_sizing_case_has_to_be_required(tmp_path):
    bad = tmp_path / "targets.yaml"
    bad.write_text(TARGETS.read_text().replace("sizing_case: mission", "sizing_case: max"))
    with pytest.raises(DesignError, match="sizing_case"):
        load_targets(bad)


def test_modules_have_to_be_real(tmp_path):
    bad = tmp_path / "targets.yaml"
    bad.write_text(TARGETS.read_text().replace("modules: [V, P]", "modules: [V, X]"))
    with pytest.raises(DesignError, match="X"):
        load_targets(bad)


def test_the_build_finds_its_parts(catalog):
    build = load_build(FIXTURES / "build.yaml", catalog)
    assert build.motor.id == "testco-m2810-900kv"
    assert build.prop.id == "testco-p10x45"
    assert build.pack.series == 6
    assert build.pack.parallel == 2
    assert build.pack.overhead == pytest.approx(0.060)
    assert build.pack.wiring_resistance == pytest.approx(0.003)
    assert [c.id for c in build.modules["P"]] == ["testco-chute", "testco-ejector"]
    assert build.thrust_table.voltage == 24.0


def test_a_build_naming_a_missing_part_fails_clearly(catalog, tmp_path):
    bad = tmp_path / "build.yaml"
    bad.write_text((FIXTURES / "build.yaml").read_text().replace("testco-camera", "testco-cam"))
    with pytest.raises(CatalogError, match="build.yaml.*testco-cam"):
        load_build(bad, catalog)


def test_the_motor_needs_a_thrust_table_for_the_prop(tmp_path):
    parts = tmp_path / "catalog"
    shutil.copytree(FIXTURES / "catalog", parts)
    (parts / "props" / "testco-p9x5.yaml").write_text(
        "type: prop\nid: testco-p9x5\nmaker: Testco\nmodel: P9x5\n"
        "source: {kind: made_up, note: test}\nmass_g: 12\ndiameter_in: 9\npitch_in: 5\nblades: 2\n"
    )
    bad = tmp_path / "build.yaml"
    text = (FIXTURES / "build.yaml").read_text()
    bad.write_text(text.replace("prop: testco-p10x45", "prop: testco-p9x5"))
    with pytest.raises(DesignError, match="thrust table.*testco-p9x5"):
        load_build(bad, load_catalog(parts, allow_made_up=True))


def test_the_pack_has_to_suit_the_motor_and_esc(catalog, tmp_path):
    bad = tmp_path / "build.yaml"
    bad.write_text((FIXTURES / "build.yaml").read_text().replace("series: 6", "series: 8"))
    with pytest.raises(DesignError, match="8S"):
        load_build(bad, catalog)


def test_variants_swap_parts_and_keep_the_rest(catalog):
    build = load_build(FIXTURES / "build.yaml", catalog)
    bigger = build.variant(parallel=3)
    assert bigger.pack.parallel == 3
    assert bigger.motor is build.motor
    assert build.pack.parallel == 2


def test_no_firmware_section_means_no_current_cap(catalog):
    assert load_build(FIXTURES / "build.yaml", catalog).current_cap is None


def test_the_firmware_can_cap_the_current(catalog, tmp_path):
    path = tmp_path / "build.yaml"
    text = (FIXTURES / "build.yaml").read_text(encoding="utf-8")
    path.write_text(text + "firmware:\n  current_cap_fraction: 0.8\n", encoding="utf-8")
    build = load_build(path, catalog)
    assert build.current_cap == pytest.approx(0.8 * 90)  # 6S2P of 45 A cells
    assert build.variant(parallel=3).current_cap == pytest.approx(0.8 * 135)  # follows the pack


def test_the_current_cap_has_to_be_above_zero(catalog, tmp_path):
    path = tmp_path / "build.yaml"
    text = (FIXTURES / "build.yaml").read_text(encoding="utf-8")
    path.write_text(text + "firmware:\n  current_cap_fraction: 0\n", encoding="utf-8")
    with pytest.raises(DesignError, match="current_cap_fraction"):
        load_build(path, catalog)
