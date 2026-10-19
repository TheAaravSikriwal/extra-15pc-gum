"""The CAD checks, each on a small made-up case with a hand-worked answer, then on the real
build. Everything in meters."""

import math
from pathlib import Path

import pytest

from pcs14.catalog import load_catalog
from pcs14.design import load_build, load_targets

ROOT = Path(__file__).resolve().parents[1]
MM = 0.001


def test_motor_overload_by_hand():
    from pcs14.cad.checks import motor_overload

    half = 0.420 / 2 / math.sqrt(2)  # motors at (±a, ±a) on a 420 mm true X
    # a weight 7.42 mm ahead of center loads the front motors 5% more than the average
    assert motor_overload((0.05 * half, 0, 0), half) == pytest.approx(0.05)
    assert motor_overload((0.003, -0.002, 0.05), half) == pytest.approx(0.005 / half)
    assert motor_overload((0, 0, 0.1), half) == 0  # height doesn't load any motor more


def test_the_best_trim_by_hand():
    from pcs14.cad.checks import best_trim

    # 2 kg drone with its center of gravity 10 mm forward; sliding the 0.8 kg pack back by
    # 25 mm moves it 10 mm, which centers it
    assert best_trim(0.010, 2.0, 0.8, home=0.030, slide=0.030) == pytest.approx(0.005)
    # 20 mm forward would need 50 mm of slide; it stops at the end of the 30 mm range
    assert best_trim(0.020, 2.0, 0.8, home=0.030, slide=0.030) == pytest.approx(0.0)


def piece(name, solid, moving=False, kind="bought"):
    from pcs14.cad.assembly import Piece

    return Piece(name, solid, kind, "base", 0.01, 0.01, moving=moving)


def test_clearance_from_a_prop_disk_by_hand():
    from build123d import Box, Cylinder, Pos

    from pcs14.cad.checks import prop_clearances

    disk = Cylinder(0.127, 0.009)
    near = piece("near", Pos(0.127 + 0.008 + 0.005, 0, 0) * Box(0.01, 0.01, 0.01))  # 8 mm away
    far = piece("far", Pos(0.127 + 0.015 + 0.005, 0, 0) * Box(0.01, 0.01, 0.01))  # 15 mm
    wire = piece("wire", Pos(0.127 + 0.015 + 0.005, 0, 0) * Box(0.01, 0.01, 0.01), moving=True)
    found = {f.parts[1]: f for f in prop_clearances([disk], [near, far, wire], 0.010, 0.020)}
    assert found["near"].value == pytest.approx(0.008)
    assert not found["near"].passed
    assert found["far"].passed
    assert not found["wire"].passed  # moving parts need 20 mm


def test_collisions_by_hand():
    from build123d import Box, Pos

    from pcs14.cad.checks import collisions

    a = piece("a", Box(0.02, 0.02, 0.02))
    b = piece("b", Pos(0.015, 0, 0) * Box(0.02, 0.02, 0.02))  # 5 mm into a
    c = piece("c", Pos(-0.02, 0, 0) * Box(0.02, 0.02, 0.02))  # just touching a
    found = collisions([a, b, c])
    assert [f.parts for f in found] == [("a", "b")]
    assert found[0].value == pytest.approx(0.005 * 0.02 * 0.02)


def test_the_parachute_cone_by_hand():
    from build123d import Box, Pos

    from pcs14.cad.checks import in_chute_cone

    mouth = (0.0, 0.0, 0.2)
    above = piece("above", Pos(0, 0, 0.35) * Box(0.02, 0.02, 0.02))
    beside = piece("beside", Pos(0.3, 0, 0.25) * Box(0.02, 0.02, 0.02))  # well outside 30 degrees
    blocked = in_chute_cone([above, beside], mouth, 0.020, 30, 0.5)
    assert blocked == ["above"]


@pytest.fixture(scope="module")
def results():
    from pcs14.cad.assembly import Drone
    from pcs14.cad.checks import check_combination
    from pcs14.cad.settings import load_settings

    build = load_build(ROOT / "design" / "build.yaml", load_catalog(ROOT / "design" / "catalog"))
    drone = Drone(build, load_settings(ROOT / "design" / "cad.yaml"))
    setups = load_targets(ROOT / "design" / "targets.yaml").combinations()
    return {s.name: check_combination(drone, s.name, s.modules) for s in setups}


def test_every_combination_gets_every_check(results):
    assert len(results) == 8
    for name, result in results.items():
        checks = {f.check for f in result.findings}
        assert {"collisions", "prop clearance", "balance"} <= checks, name
        assert result.trim_x is not None
    assert "parachute cone" in {f.check for f in results["mission"].findings}
    assert "compass distance" in {f.check for f in results["mission"].findings}


def test_the_trimmed_pack_never_hits_anything(results):
    for name, result in results.items():
        hits = [f for f in result.findings if f.check == "collisions" and "pack" in f.parts]
        assert hits == [], name


def test_the_real_layout_passes_every_check_in_every_combination(results):
    for name, result in results.items():
        failing = [f.detail for f in result.findings if not f.passed]
        assert failing == [], name


def test_the_real_drone_fuses_into_one_closed_skin_for_the_wind_tunnel():
    # a part touching another along just an edge breaks the fused skin (C's socket and the
    # fuse holders did, flush with the frame's back edge), and the CFD export refuses it
    from pcs14.cad.assembly import Drone
    from pcs14.cad.checks import trim
    from pcs14.cad.export import cfd_body, is_watertight
    from pcs14.cad.settings import load_settings

    build = load_build(ROOT / "design" / "build.yaml", load_catalog(ROOT / "design" / "catalog"))
    drone = Drone(build, load_settings(ROOT / "design" / "cad.yaml"))
    assert is_watertight(cfd_body(trim(drone, {"V", "P", "C"}).pieces))
