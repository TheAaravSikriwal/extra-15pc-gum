"""Sanity checks on design/targets.yaml, so a typo there can't quietly break things."""

from pathlib import Path

import pytest
import yaml

TARGETS = Path(__file__).resolve().parents[1] / "design" / "targets.yaml"
MODULES = {"V", "P", "C"}
SETUPS = ("base", "mission", "max")


def load():
    return yaml.safe_load(TARGETS.read_text(encoding="utf-8"))


def test_has_the_three_setups():
    assert set(load()["setups"]) == set(SETUPS)


def test_modules_are_real_modules():
    for name, setup in load()["setups"].items():
        assert set(setup["modules"]) <= MODULES, name


def test_base_is_bare_and_max_has_everything():
    setups = load()["setups"]
    assert setups["base"]["modules"] == []
    assert set(setups["max"]["modules"]) == MODULES


@pytest.mark.parametrize("key", ["min_cruise_time_min", "min_hover_time_min"])
def test_more_modules_never_means_a_stricter_flight_time(key):
    setups = load()["setups"]
    times = [setups[s][key] for s in SETUPS]
    assert times == sorted(times, reverse=True)


def test_hover_targets_sit_under_cruise():
    # A gentle cruise takes a bit less power than a hover, so hover times are lower.
    for name, setup in load()["setups"].items():
        assert setup["min_hover_time_min"] < setup["min_cruise_time_min"], name


def test_thrust_rule_can_actually_lift():
    assert load()["every_setup"]["min_thrust_to_weight"] > 1


def test_cruise_speed_is_positive():
    assert load()["cruise_speed_ms"] > 0


def test_reserve_is_a_fraction():
    assert 0 < load()["reserve_battery_fraction"] < 1


def test_sizing_case_is_a_required_setup():
    targets = load()
    case = targets["sizing_case"]
    assert case in targets["setups"]
    assert targets["setups"][case].get("required", True) is True


def test_growth_margin_is_not_negative():
    assert load()["growth_margin_g"] >= 0
