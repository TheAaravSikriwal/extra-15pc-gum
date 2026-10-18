"""Checks and verdicts: pass, marginal (only on the optimistic numbers) or fail."""

import dataclasses

import pytest

from pcs14.sizing.checks import evaluate, evaluate_setup, verdict_for
from pcs14.viz import Recorder


@pytest.mark.parametrize(
    ("nominal", "pessimistic", "verdict"),
    [(2.5, 2.2, "pass"), (2.1, 1.9, "marginal"), (1.9, 1.7, "fail")],
)
def test_verdicts_when_higher_is_better(nominal, pessimistic, verdict):
    assert verdict_for(nominal, pessimistic, limit=2.0, higher_is_better=True) == verdict


@pytest.mark.parametrize(
    ("nominal", "pessimistic", "verdict"),
    [(80, 85, "pass"), (85, 95, "marginal"), (95, 99, "fail")],
)
def test_verdicts_when_lower_is_better(nominal, pessimistic, verdict):
    assert verdict_for(nominal, pessimistic, limit=90, higher_is_better=False) == verdict


def test_a_drone_that_passes(build, targets, setups):
    base = evaluate_setup(build, targets, setups["base"])
    assert base.verdict == "pass"
    assert {c.name for c in base.checks} >= {"Hover time", "Thrust-to-weight at the reserve"}


def test_a_drone_that_is_marginal(build, targets, setups):
    # The made-up mission setup has 2.18:1 at the reserve, but only 1.96:1 pessimistic
    mission = evaluate_setup(build, targets, setups["mission"], growth_margin=0.2)
    tw = mission.check("Thrust-to-weight at the reserve")
    assert tw.nominal == pytest.approx(2.18, abs=0.01)
    assert tw.verdict == "marginal"
    assert mission.verdict == "marginal"


def test_a_drone_that_fails(build, targets, setups):
    small_pack = build.variant(parallel=1)
    mission = evaluate_setup(small_pack, targets, setups["mission"], growth_margin=0.2)
    assert mission.verdict == "fail"
    assert mission.check("Hover time").verdict == "fail"
    assert mission.check("Full-throttle current").verdict == "fail"  # 45 A is the 1P limit


def test_mission_gets_its_speed_and_wind_checks(build, targets, setups):
    mission = evaluate_setup(build, targets, setups["mission"], growth_margin=0.2)
    names = {c.name for c in mission.checks}
    assert {"Top speed at half charge", "Holds position in 10 m/s wind"} <= names
    base = evaluate_setup(build, targets, setups["base"])
    assert "Top speed at half charge" not in {c.name for c in base.checks}


def test_too_heavy_to_hover_fails_cleanly(build, targets, setups):
    heavy = dataclasses.replace(setups["max"], payload=10.0)
    result = evaluate_setup(build, targets, heavy)
    assert result.verdict == "fail"
    assert result.check("Hovers at all").verdict == "fail"


def test_the_design_verdict_is_the_worst_required_setup(build, targets):
    design = evaluate(build, targets)
    assert len(design.setups) == 8
    assert design.sizing.setup.name == "mission"
    assert design.verdict == "marginal"
    assert design.setup("mission").mass.total == pytest.approx(2.216)


def test_every_flight_can_go_into_rerun(build, targets, tmp_path):
    path = tmp_path / "sizing.rrd"
    recorder = Recorder(path=path)
    evaluate(build, targets, recorder=recorder)
    recorder.close()
    assert path.stat().st_size > 10_000


def test_a_current_cap_keeps_full_throttle_inside_the_rating(build, targets, setups):
    capped = build.variant(current_cap_fraction=0.5)  # 45 A on a 90 A pack
    base = evaluate_setup(capped, targets, setups["base"])
    current = base.check("Full-throttle current")
    assert current.nominal == 45
    assert current.verdict == "pass"
    assert "caps it at 45 A" in current.note
    assert "would pull 83 A" in current.note  # 82.19 A, rounded toward failing
    assert not current.ranked  # the cap holds it, so it says nothing about the parts


def test_without_a_cap_the_current_check_ranks(build, targets, setups):
    base = evaluate_setup(build, targets, setups["base"])
    assert base.check("Full-throttle current").ranked
