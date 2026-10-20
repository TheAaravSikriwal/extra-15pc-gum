"""The flight sim's pass/fail numbers and the safety monitor's trigger thresholds, from the
`flight_sim` section of design/targets.yaml."""

from pathlib import Path

import pytest
import yaml

from pcs14.design import DesignError, load_targets

ROOT = Path(__file__).resolve().parents[1]
TARGETS = ROOT / "design" / "targets.yaml"


def test_the_real_targets_carry_the_flight_sim_numbers():
    sim = load_targets(TARGETS).flight_sim
    assert sim.hover.max_drift_m == 0.5 and sim.hover.max_height_error_m == 0.3
    assert sim.hover.duration_s == 60
    assert sim.steps.max_settle_s == 0.5 and sim.steps.max_overshoot == pytest.approx(0.2)
    assert sim.wind.max_drift_m == 1.0 and sim.wind.max_motor_share == pytest.approx(0.9)
    assert sim.endurance.max_difference == pytest.approx(0.1)
    assert sim.payload.max_drift_m == 1.0
    assert sim.max_false_triggers == 0


def test_the_triggers_start_where_the_spec_says():
    triggers = load_targets(TARGETS).flight_sim.triggers
    assert triggers.free_fall_g == pytest.approx(0.3) and triggers.free_fall_s == pytest.approx(0.3)
    assert triggers.tumble_rate_dps == 400 and triggers.tumble_rate_s == pytest.approx(0.3)
    assert triggers.tumble_tilt_deg == 75 and triggers.tumble_tilt_s == pytest.approx(0.5)


def _with(tmp_path, change):
    data = yaml.safe_load(TARGETS.read_text(encoding="utf-8"))
    change(data["flight_sim"])
    path = tmp_path / "targets.yaml"
    path.write_text(yaml.safe_dump(data), encoding="utf-8")
    return path


def test_a_share_past_one_is_refused(tmp_path):
    def change(sim):
        sim["wind"]["max_motor_share"] = 1.5

    with pytest.raises(DesignError, match="max_motor_share"):
        load_targets(_with(tmp_path, change))


def test_a_missing_number_is_named(tmp_path):
    def change(sim):
        del sim["hover"]["max_drift_m"]

    with pytest.raises(DesignError, match="max_drift_m"):
        load_targets(_with(tmp_path, change))


def test_targets_without_a_flight_sim_section_still_load(tmp_path):
    data = yaml.safe_load(TARGETS.read_text(encoding="utf-8"))
    del data["flight_sim"]
    path = tmp_path / "targets.yaml"
    path.write_text(yaml.safe_dump(data), encoding="utf-8")
    assert load_targets(path).flight_sim is None
