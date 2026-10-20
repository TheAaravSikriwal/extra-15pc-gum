"""Grading a flight: each scenario's checks on a short synthetic log with a hand-worked answer,
including ones that fail."""

import math

import numpy as np
import pytest

from pcs14.flight import grade

DT = 0.02


def log(seconds, **series):
    t = np.arange(0, seconds, DT)
    n = len(t)
    base = {
        "position": np.zeros((n, 3)),
        "velocity": np.zeros((n, 3)),
        "rotor_speed": np.full((n, 4), 600.0),
    }
    for name, value in series.items():
        base[name] = value(t) if callable(value) else value
    return grade.FlightLog(t=t, events=series.get("events", []), **{
        k: v for k, v in base.items() if k != "events"
    })  # fmt: skip


def test_a_steady_hover_holds():
    drift = log(60, position=lambda t: np.column_stack([0.2 * np.sin(t), 0 * t, 10 + 0.1 * t / 60]))
    found = grade.hover_hold(drift, start=0, end=60, height=10, max_drift=0.5, max_height=0.3)
    assert [f.passed for f in found] == [True, True]
    assert found[0].value == pytest.approx(0.2, abs=0.01)


def test_a_wandering_hover_fails():
    wander = log(60, position=lambda t: np.column_stack([t / 60, 0 * t, 10 + 0 * t]))
    found = grade.hover_hold(wander, start=0, end=60, height=10, max_drift=0.5, max_height=0.3)
    assert not found[0].passed and found[0].value == pytest.approx(1.0, abs=0.02)


def test_a_step_response_by_hand():
    # a first-order response with a 0.1 s time constant: no overshoot, inside 5% after 3 tau
    t = np.arange(0, 2, 0.001)
    response = np.where(t < 0.5, 0.0, 1 - np.exp(-(t - 0.5) / 0.1))
    found = grade.step_response(t, response, at=0.5, size=1.0, max_settle=0.5, max_overshoot=0.2)
    settle, overshoot = found
    assert settle.value == pytest.approx(0.1 * math.log(20), abs=0.002)  # 0.3 s
    assert overshoot.value == pytest.approx(0.0, abs=1e-6) and settle.passed and overshoot.passed


def test_a_ringing_step_fails_on_overshoot():
    t = np.arange(0, 3, 0.001)
    rel = t - 0.5
    response = np.where(t < 0.5, 0.0, 1 - np.exp(-rel / 0.3) * np.cos(12 * rel))
    _, overshoot = grade.step_response(t, response, at=0.5, size=1.0, max_settle=0.5,
                                       max_overshoot=0.2)  # fmt: skip
    assert not overshoot.passed and overshoot.value > 0.2


def test_top_speed_counts_only_what_it_holds():
    fast = log(20, velocity=lambda t: np.column_stack([np.where(t > 5, 23.0, 5.0), 0 * t, 0 * t]))
    found = grade.top_speed(fast, target=22.2)
    assert found.passed and found.value == pytest.approx(23.0)
    blip = log(20, velocity=lambda t: np.column_stack([np.where(abs(t - 5) < 0.2, 30.0, 10.0),
                                                       0 * t, 0 * t]))  # fmt: skip
    assert not grade.top_speed(blip, target=22.2).passed  # 0.4 s at 30 m/s doesn't count


def test_the_wind_hold_checks_drift_and_motor_headroom():
    windy = log(30, position=lambda t: np.column_stack([0.4 + 0 * t, 0 * t, 10 + 0 * t]),
                rotor_speed=np.full((1500, 4), 700.0))  # fmt: skip
    drift, headroom = grade.wind_hold(windy, start=5, end=30, height=10, max_drift=1.0,
                                      max_motor_share=0.9, max_rot_velocity=930.0)  # fmt: skip
    assert drift.passed and headroom.passed and headroom.value == pytest.approx(700 / 930)
    straining = log(30, rotor_speed=np.full((1500, 4), 900.0))
    _, headroom = grade.wind_hold(straining, start=5, end=30, height=0, max_drift=1.0,
                                  max_motor_share=0.9, max_rot_velocity=930.0)  # fmt: skip
    assert not headroom.passed


def test_endurance_against_the_sizing_model():
    assert grade.endurance(1300, 1340, 0.1).passed
    assert not grade.endurance(1100, 1340, 0.1).passed
    # the times themselves ride along, for the report's comparison table
    assert grade.endurance(1300, 1340, 0.1).extra == {"sim_min": 1300 / 60, "sizing_min": 1340 / 60}


def test_the_safety_monitor_catching_a_real_failure(targets):
    from pcs14.safety.triggers import G, ImuSample

    limits = targets.flight_sim.triggers  # free fall: under 0.3 g for 0.3 s
    calm = [ImuSample(k * 0.004, (0, 0, G), (0, 0, 0)) for k in range(2500)]
    falling = [ImuSample(10 + k * 0.004, (0, 0, 0), (0, 0, 0)) for k in range(200)]
    found = grade.caught(calm + falling, limits, since=10.0)
    assert found.passed and found.value == pytest.approx(0.3, abs=0.01)
    assert "free fall" in found.detail
    assert not grade.caught(calm, limits, since=5.0).passed  # nothing to catch, nothing caught


def test_a_failsafe_has_to_happen_in_order():
    events = [(10.0, "link lost"), (11.0, "return"), (40.0, "landed")]
    assert grade.sequence(events, ["link lost", "return", "landed"], "lost link").passed
    out_of_order = [(10.0, "link lost"), (11.0, "landed"), (40.0, "return")]
    assert not grade.sequence(out_of_order, ["link lost", "return", "landed"], "lost link").passed


def test_the_chute_fires_only_after_the_motors_stop_and_reports_the_height_lost():
    t = np.arange(0, 20, DT)
    # falling from 60 m: free fall until the canopy holds, then a steady 4.6 m/s
    z = np.where(t < 5, 60.0, np.maximum(60 - 0.5 * 9.8 * np.minimum(t - 5, 1.2) ** 2
                                         - 4.6 * np.maximum(t - 6.2, 0), 0))  # fmt: skip
    vz = np.gradient(z, t)
    drop = grade.FlightLog(t=t, position=np.column_stack([0 * t, 0 * t, z]),
                           velocity=np.column_stack([0 * t, 0 * t, vz]),
                           rotor_speed=np.where(t[:, None] < 4.9, 600.0, 0.0) * np.ones((1, 4)),
                           events=[(4.9, "motors stopped"), (5.0, "chute fired")])  # fmt: skip
    order, lost = grade.chute(drop)
    assert order.passed
    # the height lost until the descent settles: the 1.2 s of free fall
    assert lost.value == pytest.approx(0.5 * 9.8 * 1.2**2, abs=0.3)
    early = grade.FlightLog(t=t, position=drop.position, velocity=drop.velocity,
                            rotor_speed=drop.rotor_speed,
                            events=[(5.0, "chute fired"), (5.2, "motors stopped")])  # fmt: skip
    assert not grade.chute(early)[0].passed
    # what counts is the canopy leaving: 0.2 s after firing, the motors have just stopped...
    assert grade.chute(early, ejection_s=0.2)[0].passed
    # ...but not with a quicker ejection
    assert not grade.chute(early, ejection_s=0.1)[0].passed


def test_no_fly_away():
    home = log(30, position=lambda t: np.column_stack([t, 0 * t, 0 * t]),
               events=[(29.0, "landed")])  # fmt: skip
    assert grade.ends_safely(home, radius=100).passed
    gone = log(30, position=lambda t: np.column_stack([10 * t, 0 * t, 50 + 0 * t]))
    assert not grade.ends_safely(gone, radius=100).passed


def test_no_fly_away_counted_from_when_the_failure_hit():
    # flew 200 m out at 10 m/s, then drifted 5 m while coming down from 30 m
    def path(t):
        east = np.minimum(t, 20) * 10 + np.maximum(t - 20, 0) / 2
        up = np.where(t < 20, 30, np.maximum(30 - 3 * (t - 20), 0))
        return np.column_stack([east, 0 * t, up])

    away = log(30, position=path)
    assert not grade.ends_safely(away, radius=30).passed  # far from home...
    found = grade.ends_safely(away, radius=30, since=20.0)  # ...but not from the failure
    assert found.passed and found.value == pytest.approx(5.0, abs=0.05)


def descent(seconds, height):
    """A log coming straight down: `height(t)` m, with the matching vertical speed."""

    def position(t):
        return np.column_stack([0 * t, 0 * t, np.maximum(height(t), 0)])

    def velocity(t):
        up = np.gradient(np.maximum(height(t), 0), t)
        return np.column_stack([0 * t, 0 * t, up])

    return log(seconds, position=position, velocity=velocity)


def test_a_touchdown_by_hand():
    # down from 10 m at 0.7 m/s: a controlled landing
    found = grade.touchdown(descent(20, lambda t: 10 - 0.7 * t), max_speed=2.0)
    assert found.passed and found.value == pytest.approx(0.7, abs=0.01)
    # falling from 10 m: about 14 m/s at the ground
    found = grade.touchdown(descent(3, lambda t: 10 - 4.9 * t**2), max_speed=2.0)
    assert not found.passed and found.value == pytest.approx(14.0, abs=0.3)
    hovering = log(5, position=lambda t: np.column_stack([0 * t, 0 * t, 5 + 0 * t]))
    assert not grade.touchdown(hovering, max_speed=2.0).passed


def test_false_triggers_counted_on_a_healthy_flight():
    from pcs14.design import TriggerThresholds
    from pcs14.safety.triggers import G, ImuSample

    limits = TriggerThresholds(
        free_fall_g=0.3,
        free_fall_s=0.3,
        tumble_rate_dps=400,
        tumble_rate_s=0.3,
        tumble_tilt_deg=75,
        tumble_tilt_s=0.5,
    )
    calm = [ImuSample(k * 0.004, (0, 0, G), (0, 0, 0)) for k in range(2500)]
    assert grade.false_triggers(calm, limits, allowed=0).passed
    dropped = calm + [ImuSample(10 + k * 0.004, (0, 0, 0), (0, 0, 0)) for k in range(200)]
    found = grade.false_triggers(dropped, limits, allowed=0)
    assert not found.passed and found.value == 1
