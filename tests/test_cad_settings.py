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


def test_every_placed_part_is_in_the_build(settings, build):
    ids = {part.id for part in [build.esc, *build.base]}
    for module in build.modules.values():
        ids |= {part.id for part in module}
    assert set(settings.place) - ids == set()


def test_every_bought_part_has_a_spot(settings, build):
    parts = [build.esc, *build.base, *[p for m in build.modules.values() for p in m]]
    needs = {p.id for p in parts if p.cad.shape not in ("printed", "routed")}
    assert needs - set(settings.place) == set()


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
