"""design/cad.yaml: the CAD's design inputs, as objects."""

from pathlib import Path

import pytest

from pcs14.catalog import load_catalog
from pcs14.design import load_build

ROOT = Path(__file__).resolve().parents[1]
CAD = ROOT / "design" / "cad.yaml"


@pytest.fixture(scope="module")
def settings():
    from pcs14.cad.settings import load_settings

    return load_settings(CAD)


@pytest.fixture(scope="module")
def build():
    return load_build(ROOT / "design" / "build.yaml", load_catalog(ROOT / "design" / "catalog"))


def test_the_check_limits_match_the_spec(settings):
    checks = settings.checks
    assert checks.max_motor_overload == 0.05
    assert checks.rigid_clearance == pytest.approx(0.010)
    assert checks.moving_clearance == pytest.approx(0.020)
    assert checks.chute_cone_half_angle_deg == 30
    assert checks.chute_cone_height == pytest.approx(0.500)


def listed(build):
    """Where each part is listed: base or a module (a part can be in more than one)."""
    where = {build.esc.id: {"base"}}
    for part in build.base:
        where.setdefault(part.id, set()).add("base")
    for module, parts in build.modules.items():
        for part in parts:
            where.setdefault(part.id, set()).add(module)
    return where


def test_every_placed_part_is_in_the_build(settings, build):
    where = listed(build)
    for spot in settings.spots():
        assert spot.part_id in where, spot.name
        if spot.module is not None:
            assert spot.module in where[spot.part_id], spot.name


def test_every_bought_part_has_a_spot_wherever_its_listed(settings, build):
    every = [build.esc, *build.base, *build.all_module_parts()]
    parts = {p.id: p for p in every}
    where = listed(build)
    spots = settings.spots()
    for part_id, places in where.items():
        if parts[part_id].cad.shape in ("printed", "routed"):
            continue
        mine = [s for s in spots if s.part_id == part_id]
        if len(places) == 1:
            assert mine, part_id
        else:
            assert {s.module for s in mine} == places, part_id


def test_a_part_in_two_modules_gets_a_spot_in_each():
    from pcs14.cad.settings import parse_spots

    spots = parse_spots({"node@P": {"at_mm": [1, 0, 0]}, "node@C": {"at_mm": [2, 0, 0]}})
    assert [(s.name, s.part_id, s.module, s.share) for s in spots] == [
        ("node@P", "node", "P", 1.0),
        ("node@C", "node", "C", 1.0),
    ]


def test_a_part_at_several_spots_shares_its_weight():
    from pcs14.cad.settings import parse_spots

    spots = parse_spots({"socket": [{"at_mm": [0, 0, 0]}, {"at_mm": [1, 0, 0]}]})
    assert [(s.name, s.module, s.share) for s in spots] == [
        ("socket 1", None, 0.5),
        ("socket 2", None, 0.5),
    ]
    assert spots[1].placement.at == pytest.approx((0.001, 0, 0))


def test_a_spot_naming_a_module_that_doesnt_exist_fails():
    from pcs14.cad.settings import parse_spots

    with pytest.raises(ValueError, match="X"):
        parse_spots({"node@X": {"at_mm": [0, 0, 0]}})


def test_places_come_out_in_meters(settings):
    lidar = settings.place["benewake-tf-luna"]
    assert lidar.at == pytest.approx((0.135, 0, -0.003))
    assert lidar.turn_deg == (180, 0, 0)


def test_every_material_used_is_defined(settings):
    used = {
        settings.legs.material,
        settings.rail.material,
        settings.gps_mast.material,
        settings.v_housing.material,
        settings.p_holder.material,
    }
    assert used <= set(settings.materials)


def test_every_wire_has_a_route(settings):
    assert len(settings.wires) >= 10
    for wire in settings.wires:
        assert len(wire.path) >= 2, wire.name
        assert wire.diameter > 0


def test_a_broken_settings_file_fails_clearly(tmp_path):
    from pcs14.cad.settings import SettingsError, load_settings

    text = CAD.read_text(encoding="utf-8").replace("checks:", "chekcs:", 1)
    broken = tmp_path / "cad.yaml"
    broken.write_text(text, encoding="utf-8")
    with pytest.raises(SettingsError, match="checks"):
        load_settings(broken)
