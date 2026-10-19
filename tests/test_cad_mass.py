"""Mass properties: each part's weight spread over its solid, added up into a weight, a center
of gravity and an inertia, for every module combination."""

from pathlib import Path

import pytest

from pcs14.catalog import load_catalog
from pcs14.design import load_build, load_targets
from pcs14.sizing.mass import mass_budget

ROOT = Path(__file__).resolve().parents[1]


def test_two_boxes_by_hand():
    from build123d import Box, Pos

    from pcs14.cad.assembly import Piece
    from pcs14.cad.mass import mass_properties

    side = 0.1
    a = Piece("a", Box(side, side, side), "bought", "base", 1.0, 1.0)
    b = Piece("b", Pos(0.3, 0, 0) * Box(side, side, side), "bought", "base", 1.0, 1.0)
    props = mass_properties([a, b])
    assert props.mass == pytest.approx(2.0)
    assert props.center == pytest.approx((0.15, 0, 0))
    own = 1.0 * (side**2 + side**2) / 12  # a cube about its own center
    assert props.inertia[0][0] == pytest.approx(2 * own)  # the x axis runs through both
    assert props.inertia[1][1] == pytest.approx(2 * (own + 1.0 * 0.15**2))  # parallel axis
    assert props.inertia[2][2] == pytest.approx(2 * (own + 1.0 * 0.15**2))
    assert props.inertia[0][1] == pytest.approx(0, abs=1e-12)


def test_a_piece_with_no_weight_doesnt_move_anything():
    from build123d import Box, Pos

    from pcs14.cad.assembly import Piece
    from pcs14.cad.mass import mass_properties

    a = Piece("a", Box(0.1, 0.1, 0.1), "bought", "base", 1.0, 1.0)
    ghost = Piece("ghost", Pos(5, 0, 0) * Box(0.1, 0.1, 0.1), "wire", "base", 0.0, 0.0)
    assert mass_properties([a, ghost]).center == pytest.approx((0, 0, 0))


@pytest.fixture(scope="module")
def drone():
    from pcs14.cad.assembly import Drone
    from pcs14.cad.settings import load_settings

    build = load_build(ROOT / "design" / "build.yaml", load_catalog(ROOT / "design" / "catalog"))
    return Drone(build, load_settings(ROOT / "design" / "cad.yaml"))


def test_the_budget_weights_match_the_sizing_model_for_every_combination(drone):
    from pcs14.cad.mass import mass_properties

    for setup in load_targets(ROOT / "design" / "targets.yaml").combinations():
        assembly = drone.combination(setup.modules)
        sizing = mass_budget(drone.build, setup).total - setup.payload
        assert mass_properties(assembly.pieces, budget=True).mass == pytest.approx(sizing), (
            setup.name
        )


def test_the_cads_own_weights_differ_only_by_the_printed_parts(drone):
    from pcs14.cad.mass import mass_properties

    assembly = drone.combination({"V", "P"})
    cad = mass_properties(assembly.pieces).mass
    budget = mass_properties(assembly.pieces, budget=True).mass
    printed = [p for p in assembly.pieces if p.kind == "printed"]
    difference = sum(p.mass - p.budget_mass for p in printed)
    # the catalog keeps each module's hardware to 0.1 g, so the hardware can differ by up to
    # 0.05 g a module on top of that
    assert abs((cad - budget) - difference) <= 3 * 0.05e-3
