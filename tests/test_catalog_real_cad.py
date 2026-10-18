"""The real catalog's cad blocks: every part in the build can be modeled, and says where its
dimensions came from and whether a CAD model of it already exists."""

from pathlib import Path

import pytest

from pcs14.catalog import load_catalog
from pcs14.design import load_build

ROOT = Path(__file__).resolve().parents[1]


@pytest.fixture(scope="module")
def build():
    catalog = load_catalog(ROOT / "design" / "catalog")
    return load_build(ROOT / "design" / "build.yaml", catalog)


def parts(build):
    every = [build.motor, build.prop, build.esc, build.frame, build.pack.cell, *build.base]
    for module in build.modules.values():
        every += module
    return every


def test_every_part_in_the_build_has_a_cad_block(build):
    missing = [part.id for part in parts(build) if part.cad is None]
    assert missing == []


def test_every_part_was_checked_for_an_existing_cad_model(build):
    for part in parts(build):
        existing = part.cad.existing
        assert existing.checked is not None, part.id
        if existing.found != "none":
            assert existing.url and existing.terms, part.id


def test_the_parts_i_design_are_marked_printed(build):
    printed = sorted(part.id for part in parts(build) if part.cad.shape == "printed")
    assert printed == [
        "battery-tray",
        "camera-bracket",
        "gps-mast",
        "landing-legs",
        "lidar-bracket",
        "module-mount",
        "p-mount",
        "remote-id-mount",
        "safety-monitor-carrier",
        "v-housing",
    ]


def test_printed_weights_come_from_the_cad(build):
    for part in parts(build):
        if part.cad.shape == "printed":
            assert part.source.kind.value == "cad", part.id


def test_wiring_comes_from_the_wire_routes(build):
    routed = sorted(part.id for part in parts(build) if part.cad.shape == "routed")
    assert routed == ["base-wiring", "rpi-camera-cable-standard-mini"]


def test_the_pieces_the_research_found_missing_are_in_the_build(build):
    ids = {part.id for part in parts(build)}
    assert {"rpi-camera-cable-standard-mini", "halow-antenna-915"} <= ids
