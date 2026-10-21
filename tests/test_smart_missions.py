"""Plain-English missions (#26): the deterministic checker every plan goes through, and the
planner that asks a language model for the plan. The checker is the contract: it's tested on
plans that break each rule. The model only ever writes plans."""

import json

import pytest

from pcs14.smart import missions


def plan(*points, end="return"):
    return missions.Plan(name="made up", waypoints=[
        missions.Waypoint(north_m=n, east_m=e, height_m=h, speed_ms=v) for n, e, h, v in points
    ], end=end)  # fmt: skip


def check(p, profile="us-recreational", chute=True, battery_wh=120.0):
    return missions.check(p, missions.Drone(chute=chute, battery_wh=battery_wh, reserve_wh=24.0,
                                            power=lambda v: 300.0, max_speed_ms=15.0),
                          missions.PROFILES[profile])  # fmt: skip


def test_a_plan_inside_every_limit_passes():
    found = check(plan((100, 0, 40, 8), (100, 100, 40, 8)))
    assert found.ok and found.problems == []
    assert 0 < found.energy_wh < 120


def test_each_rule_catches_its_own_problem():
    assert any("ceiling" in p for p in check(plan((0, 0, 150, 5))).problems)  # 400 ft
    assert not check(plan((0, 0, 150, 5)), profile="max").problems  # no ceiling in max
    assert any("parachute rule" in p for p in check(plan((0, 0, 40, 5)), chute=False).problems)
    assert any("faster" in p for p in check(plan((50, 0, 20, 25))).problems)
    # a long way out on a small battery: the energy, home and reserve included, doesn't fit
    far = check(plan((4000, 0, 30, 10), (8000, 0, 30, 10)), battery_wh=60.0)
    assert any("energy" in p for p in far.problems) and not far.ok


def test_the_planner_hands_whatever_the_model_writes_to_the_checker():
    written = json.dumps({"name": "look at the barn", "end": "return", "waypoints": [
        {"north_m": 120, "east_m": 30, "height_m": 35, "speed_ms": 6, "hold_s": 10}]})  # fmt: skip
    found = missions.plan_from_words("fly to the barn and look at it", ask=lambda prompt: written)
    assert found.waypoints[0].north_m == 120 and found.waypoints[0].hold_s == 10


def test_a_checked_plan_is_saved_with_its_words_its_check_and_who_approved_it(tmp_path):
    p = plan((100, 0, 40, 8))
    checked = check(p)
    path = missions.save(tmp_path / "plan.json", "fly north", p, checked, approved_by=None)
    found = missions.load(path)
    assert found.words == "fly north" and found.plan.waypoints[0].north_m == 100
    assert found.ok and found.approved_by is None
    assert not found.flyable  # nobody has approved it yet
    approved = missions.approve(path, by="the test script")
    assert approved.flyable and approved.approved_by == "the test script"


def test_a_plan_the_checker_refused_can_never_be_approved(tmp_path):
    p = plan((0, 0, 150, 5))
    path = missions.save(tmp_path / "plan.json", "go high", p, check(p), approved_by=None)
    with pytest.raises(missions.NotFlyable):
        missions.approve(path, by="the test script")


def test_the_drone_the_checker_sees_is_the_build_with_its_pack_and_reserve():
    from pathlib import Path

    from pcs14.catalog import load_catalog
    from pcs14.design import load_build, load_targets

    root = Path(__file__).resolve().parents[1] / "design"
    build = load_build(root / "build.yaml", load_catalog(root / "catalog"))
    targets = load_targets(root / "targets.yaml")
    mission = next(s for s in targets.combinations() if s.name == "mission")
    drone = missions.drone_for(build, targets, mission)
    assert drone.chute  # mission carries P
    assert 150 < drone.battery_wh < 250  # a 6S2P pack of 4.5 Ah cells: about 194 Wh
    assert drone.reserve_wh == pytest.approx(drone.battery_wh * targets.reserve_fraction)
    assert drone.power(10.0) >= drone.power(0.0)  # never cheaper than hovering


def test_a_model_that_writes_nonsense_gets_no_plan():
    with pytest.raises(missions.NoPlan):
        missions.plan_from_words("fly", ask=lambda prompt: "sure! here's a plan: go north")
