"""The safety monitor's automatic triggers, the Python reference version: free fall and
tumbling, from IMU samples. Step 5's Teensy firmware has to give the same answers."""

import math

import pytest

from pcs14.design import TriggerThresholds
from pcs14.safety.triggers import G, ImuSample, triggers

LIMITS = TriggerThresholds(
    free_fall_g=0.3,
    free_fall_s=0.3,
    tumble_rate_dps=400,
    tumble_rate_s=0.3,
    tumble_tilt_deg=75,
    tumble_tilt_s=0.5,
)
DT = 0.004  # the IMU at 250 Hz


def trace(seconds, accel=(0.0, 0.0, G), gyro=(0.0, 0.0, 0.0), tilt=0.0, start=0.0):
    return [ImuSample(start + k * DT, accel, gyro, tilt) for k in range(int(round(seconds / DT)))]


def hover(seconds, start=0.0):
    return trace(seconds, start=start)


def test_a_steady_hover_triggers_nothing():
    assert triggers(hover(10), LIMITS) == []


def test_a_drop_triggers_free_fall_once_it_has_lasted():
    samples = hover(1) + trace(1, accel=(0.0, 0.0, 0.5), start=1)  # 0.05 g: falling
    found = triggers(samples, LIMITS)
    assert [t.kind for t in found] == ["free fall"]
    assert found[0].at == pytest.approx(1.3, abs=DT)


def test_a_throttle_chop_shorter_than_the_window_doesnt():
    samples = hover(1) + trace(0.2, accel=(0.0, 0.0, 0.5), start=1) + hover(1, start=1.2)
    assert triggers(samples, LIMITS) == []


def test_a_punch_out_doesnt():
    assert triggers(hover(1) + trace(1, accel=(0.0, 0.0, 3 * G), start=1), LIMITS) == []


def test_a_tumble_triggers_on_rate():
    spin = math.radians(600)
    found = triggers(hover(1) + trace(1, gyro=(spin, 0.0, 0.0), start=1), LIMITS)
    assert [t.kind for t in found] == ["tumble rate"]
    assert found[0].at == pytest.approx(1.3, abs=DT)


def test_a_fast_yaw_under_the_rate_doesnt():
    yaw = math.radians(360)
    assert triggers(trace(2, gyro=(0.0, 0.0, yaw)), LIMITS) == []


def test_a_flipped_drone_triggers_on_tilt_and_a_hard_lean_doesnt():
    over = triggers(hover(1) + trace(1, tilt=math.radians(80), start=1), LIMITS)
    assert [t.kind for t in over] == ["tumble tilt"]
    assert over[0].at == pytest.approx(1.5, abs=DT)
    assert triggers(trace(2, tilt=math.radians(60)), LIMITS) == []


def test_it_rearms_after_the_condition_clears():
    drop = trace(0.5, accel=(0.0, 0.0, 0.5))
    samples = drop + hover(1, start=0.5) + trace(0.5, accel=(0.0, 0.0, 0.5), start=1.5)
    assert [t.kind for t in triggers(samples, LIMITS)] == ["free fall", "free fall"]
