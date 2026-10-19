"""The screws, nuts and spacers: weighed from their standard sizes, put on the parts they hold in
the CAD, and written into the catalog so the sizing model counts them."""

import math
import shutil
from pathlib import Path

import pytest
import yaml

from pcs14.catalog import load_catalog
from pcs14.design import load_build

ROOT = Path(__file__).resolve().parents[1]
STEEL = 7.85  # g/cm3


def test_an_m3_socket_head_screw_by_hand():
    from pcs14.cad import hardware

    # ISO 4762 M3: a 5.5 mm head 3 mm tall less its 2.5 mm hex socket 1.3 mm deep, and a shank
    # taken at the thread's pitch diameter, 2.675 mm
    head = math.pi / 4 * 5.5**2 * 3 - math.sqrt(3) / 2 * 2.5**2 * 1.3
    shank = math.pi / 4 * 2.675**2 * 12
    assert hardware.screw_volume("M3", 12) * 1e9 == pytest.approx(head + shank, rel=1e-6)
    assert (head + shank) / 1000 * STEEL == pytest.approx(1.03, abs=0.01)  # about a gram


def test_an_m3_nut_by_hand():
    from pcs14.cad import hardware

    # ISO 4032 M3: 5.5 mm across flats, 2.4 mm tall, a 3 mm hole
    hexagon = math.sqrt(3) / 2 * 5.5**2
    assert hardware.nut_volume("M3") * 1e9 == pytest.approx((hexagon - math.pi / 4 * 9) * 2.4)


def settings_with(items):
    from pcs14.cad.settings import load_settings

    settings = load_settings(ROOT / "design" / "cad.yaml")
    from pcs14.cad.settings import Fastener

    return settings.model_copy(update={"hardware": [Fastener.model_validate(i) for i in items]})


def test_each_item_weighs_its_count_in_its_material():
    from pcs14.cad import hardware

    settings = settings_with(
        [
            {"what": "screw", "size": "M3", "length_mm": 12, "count": 8, "material": "steel",
             "holds": "landing-legs"},
            {"what": "grommet", "count": 8, "grams": 0.15, "holds": "holybro-tekko32-f4-50a"},
        ]
    )  # fmt: skip
    parts = hardware.by_part(settings)
    each = hardware.screw_volume("M3", 12) * settings.materials["steel"].density
    assert parts["landing-legs"] == pytest.approx(8 * each)
    assert parts["holybro-tekko32-f4-50a"] == pytest.approx(8 * 0.15e-3)


def test_the_cad_puts_the_hardware_on_the_parts_it_holds():
    from pcs14.cad import hardware
    from pcs14.cad.assembly import Drone
    from pcs14.cad.settings import load_settings

    build = load_build(ROOT / "design" / "build.yaml", load_catalog(ROOT / "design" / "catalog"))
    plain = load_settings(ROOT / "design" / "cad.yaml").model_copy(update={"hardware": []})
    settings = settings_with(
        [{"what": "screw", "size": "M3", "length_mm": 12, "count": 8, "material": "steel",
          "holds": "landing-legs"}]
    )  # fmt: skip
    before = Drone(build, plain).combination(set())
    after = Drone(build, settings).combination(set())
    legs = [p for p in after.pieces if p.part_id == "landing-legs"]
    added = sum(p.mass for p in legs) - sum(
        p.mass for p in before.pieces if p.part_id == "landing-legs"
    )
    assert added == pytest.approx(hardware.by_part(settings)["landing-legs"])


def test_every_item_holds_a_part_in_the_build():
    from pcs14.cad.settings import load_settings
    from pcs14.electrical.validate import listed_in

    build = load_build(ROOT / "design" / "build.yaml", load_catalog(ROOT / "design" / "catalog"))
    listed = listed_in(build)
    for item in load_settings(ROOT / "design" / "cad.yaml").hardware:
        assert item.holds in listed, item.holds


@pytest.fixture
def copy(tmp_path):
    shutil.copytree(ROOT / "design" / "catalog", tmp_path / "catalog")
    shutil.copy(ROOT / "design" / "build.yaml", tmp_path / "build.yaml")
    return tmp_path


def test_the_catalog_takes_the_hardware_by_module(copy):
    from pcs14.cad import hardware
    from pcs14.cad.catalog_update import update_hardware

    # start from a catalog and build without any hardware
    for part_id in hardware.HARDWARE_PARTS.values():
        (copy / "catalog" / "components" / f"{part_id}.yaml").unlink(missing_ok=True)
    build = copy / "build.yaml"
    lines = build.read_text(encoding="utf-8").splitlines()
    kept = [x for x in lines if "-hardware" not in x]
    build.write_text("\n".join(kept) + "\n", encoding="utf-8")

    masses = {"base": 0.0321, "V": 0.0027, "P": 0.0018}
    changed = update_hardware(masses, copy / "catalog", copy / "build.yaml")
    assert {p.name for p in changed} >= {"base-hardware.yaml", "v-hardware.yaml", "build.yaml"}
    catalog = load_catalog(copy / "catalog")
    assert catalog.component("base-hardware").mass == pytest.approx(0.0321)
    assert "design/cad.yaml" in catalog.component("p-hardware").source.note
    build = load_build(copy / "build.yaml", catalog)
    assert "base-hardware" in {p.id for p in build.base}
    assert "v-hardware" in {p.id for p in build.modules["V"]}
    assert "c-hardware" not in yaml.safe_load((copy / "build.yaml").read_text())["modules"]["C"]
    # running it again changes nothing
    assert update_hardware(masses, copy / "catalog", copy / "build.yaml") == []
    assert hardware.HARDWARE_PARTS["base"] == "base-hardware"
