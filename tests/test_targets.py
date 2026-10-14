"""Sanity checks on design/targets.yaml, so a typo there can't quietly break things."""

from pathlib import Path

import yaml

TARGETS = Path(__file__).resolve().parents[1] / "design" / "targets.yaml"
MODULES = {"V", "P", "C"}


def load():
    return yaml.safe_load(TARGETS.read_text(encoding="utf-8"))


def test_has_the_three_setups():
    assert set(load()["setups"]) == {"base", "mission", "max"}


def test_modules_are_real_modules():
    for name, setup in load()["setups"].items():
        assert set(setup["modules"]) <= MODULES, name


def test_base_is_bare_and_max_has_everything():
    setups = load()["setups"]
    assert setups["base"]["modules"] == []
    assert set(setups["max"]["modules"]) == MODULES


def test_more_modules_never_means_a_stricter_flight_time():
    setups = load()["setups"]
    times = [setups[s]["min_flight_time_min"] for s in ("base", "mission", "max")]
    assert times == sorted(times, reverse=True)


def test_reserve_is_a_fraction():
    assert 0 < load()["reserve_battery_fraction"] < 1
