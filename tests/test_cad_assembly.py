"""The assembly: every part placed, for all eight module combinations, plus the wire routes."""

import math
from pathlib import Path

import pytest

from pcs14.catalog import load_catalog
from pcs14.design import load_build, load_targets

ROOT = Path(__file__).resolve().parents[1]
MM = 0.001


@pytest.fixture(scope="module")
def drone():
    from pcs14.cad.assembly import Drone
    from pcs14.cad.settings import load_settings

    build = load_build(ROOT / "design" / "build.yaml", load_catalog(ROOT / "design" / "catalog"))
    return Drone(build, load_settings(ROOT / "design" / "cad.yaml"))


@pytest.fixture(scope="module")
def setups():
    return {s.name: s for s in load_targets(ROOT / "design" / "targets.yaml").combinations()}


def names(assembly):
    return {piece.name for piece in assembly.pieces}


def test_every_module_combination_builds(drone, setups):
    assert len(setups) == 8
    for setup in setups.values():
        assembly = drone.combination(setup.modules)
        assert assembly.pieces, setup.name


def test_modules_bring_their_parts(drone, setups):
    base = names(drone.combination(setups["base"].modules))
    mission = names(drone.combination(setups["mission"].modules))
    full = names(drone.combination(setups["max"].modules))
    assert "fruity-chutes-harrier-40-42" not in base and "v housing" not in base
    assert {"fruity-chutes-harrier-40-42", "v housing", "rpi-5-4gb"} <= mission
    assert "claws-placeholder" not in mission and "claws-placeholder" in full
    assert "wire camera cable" in mission and "wire camera cable" not in base
    assert {"motor front left", "prop back right", "frame", "pack", "battery tray"} <= base


def test_nothing_floats(drone, setups):
    from pcs14.cad.assembly import floating

    assembly = drone.combination(setups["max"].modules)
    assert floating(assembly) == []


def test_every_wire_has_a_length(drone, setups):
    assembly = drone.combination(setups["max"].modules)
    lengths = assembly.wire_lengths
    assert len(lengths) == len(drone.settings.wires)
    battery = next(w for w in drone.settings.wires if w.name == "battery leads")
    expected = sum(math.dist(a, b) for a, b in zip(battery.path, battery.path[1:], strict=False))
    assert lengths["battery leads"] == pytest.approx(expected)
    assert all(length > 0 for length in lengths.values())


def test_the_pack_slides_to_trim(drone, setups):
    modules = setups["mission"].modules
    home = drone.combination(modules)
    moved = drone.combination(modules, pack_x=home.pack_x + 0.02)
    pack = {p.name: p for p in moved.pieces}["pack"].solid.bounding_box()
    before = {p.name: p for p in home.pieces}["pack"].solid.bounding_box()
    assert pack.center().X - before.center().X == pytest.approx(0.02)


def test_the_prop_disks_come_along_for_the_checks(drone, setups):
    assembly = drone.combination(setups["base"].modules)
    assert len(assembly.prop_disks) == 4
    disk = assembly.prop_disks[0].bounding_box()
    assert disk.size.X / MM == pytest.approx(254)


def test_a_part_in_two_modules_comes_with_each(drone, setups):
    p_only = names(drone.combination(setups["P"].modules))
    full = names(drone.combination(setups["max"].modules))
    assert "ark-cannode@P" in p_only and "ark-cannode@C" not in p_only
    assert {"ark-cannode@P", "ark-cannode@C"} <= full


def test_a_part_at_several_spots_splits_its_weight(drone, setups):
    full = drone.combination(setups["max"].modules)
    sockets = [p for p in full.pieces if p.part_id == "module-socket"]
    assert len(sockets) == 3
    assert sum(p.mass for p in sockets) == pytest.approx(drone.build_part_mass("module-socket"))
