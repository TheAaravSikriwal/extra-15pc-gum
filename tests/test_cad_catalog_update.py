"""Closing the loop: the printed parts' weights go back into the catalog, marked as from the
CAD, and parts the catalog didn't have yet join it and the build."""

import shutil
from pathlib import Path

import pytest
import yaml

from pcs14.catalog import SourceKind, load_catalog
from pcs14.design import load_build

ROOT = Path(__file__).resolve().parents[1]


@pytest.fixture
def copy(tmp_path):
    shutil.copytree(ROOT / "design" / "catalog", tmp_path / "catalog")
    shutil.copy(ROOT / "design" / "build.yaml", tmp_path / "build.yaml")
    return tmp_path


def printed(name, grams, catalog_id, module="base", material="petg_cf"):
    from build123d import Box

    from pcs14.cad.printed import PrintedPart

    return PrintedPart(
        name,
        ((Box(0.01, 0.01, 0.01), material),),
        material,
        0.002,
        (0, 0, -1),
        module,
        catalog_id,
        mass=grams / 1000,
    )


def test_known_parts_get_their_weight_from_the_cad(copy):
    from pcs14.cad.catalog_update import update_catalog

    motor_before = (copy / "catalog" / "motors" / "emax-e3-2814-850kv.yaml").read_bytes()
    update_catalog(
        [printed("module rail", 13.4, "module-mount")], copy / "catalog", copy / "build.yaml"
    )
    part = load_catalog(copy / "catalog").component("module-mount")
    assert part.mass_g == pytest.approx(13.4)
    assert part.source.kind is SourceKind.CAD
    assert "module rail" in part.source.note
    assert (copy / "catalog" / "motors" / "emax-e3-2814-850kv.yaml").read_bytes() == motor_before


def test_parts_sharing_an_entry_add_up(copy):
    from pcs14.cad.catalog_update import update_catalog

    legs = [printed(f"leg {k}", 6.6, "landing-legs", material="tpu") for k in range(4)]
    update_catalog(legs, copy / "catalog", copy / "build.yaml")
    part = load_catalog(copy / "catalog").component("landing-legs")
    assert part.mass_g == pytest.approx(26.4)
    assert part.cad.shape == "printed"


def test_new_parts_join_the_build_in_their_module(copy):
    from pcs14.cad.catalog_update import update_catalog

    update_catalog(
        [
            printed("battery tray", 27.0, "battery-tray"),
            printed("camera bracket", 2.6, "camera-bracket", "V"),
        ],
        copy / "catalog",
        copy / "build.yaml",
    )
    build = load_build(copy / "build.yaml", load_catalog(copy / "catalog"))
    assert "battery-tray" in {p.id for p in build.base}
    assert "camera-bracket" in {p.id for p in build.modules["V"]}
    raw = yaml.safe_load((copy / "build.yaml").read_text(encoding="utf-8"))
    assert raw["base"].count("battery-tray") == 1


def test_running_it_twice_changes_nothing_more(copy):
    from pcs14.cad.catalog_update import update_catalog

    parts = [
        printed("battery tray", 27.0, "battery-tray"),
        printed("module rail", 13.4, "module-mount"),
    ]
    update_catalog(parts, copy / "catalog", copy / "build.yaml")
    first = {p: p.read_bytes() for p in copy.rglob("*.yaml")}
    update_catalog(parts, copy / "catalog", copy / "build.yaml")
    assert {p: p.read_bytes() for p in copy.rglob("*.yaml")} == first
