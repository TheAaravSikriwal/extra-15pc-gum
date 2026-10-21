"""Self-tuning (#21): the inertia from a small excitation, and the gains that follow from it.
My rate loop asks for an angular acceleration and multiplies by the inertia it believes, so if
the drone turns slower than asked, its inertia is bigger than believed, by that ratio."""

import numpy as np
import pytest

from pcs14.smart import tuning


def made_up_doublet(true_inertia, believed, noise=0.0, seed=1):
    rng = np.random.default_rng(seed)
    t = np.arange(0.0, 0.6, 0.004)
    asked = np.where(t < 0.15, 40.0, np.where(t < 0.3, -40.0, 0.0))  # rad/s^2, a doublet
    actual = asked * believed / true_inertia
    rate = np.cumsum(actual) * 0.004 + rng.normal(0, noise, t.size)
    return t, rate, asked


def test_a_heavier_drone_turns_slower_and_the_identification_says_how_much():
    t, rate, asked = made_up_doublet(true_inertia=0.05, believed=0.04)
    found = tuning.identify_inertia(t, rate, asked, believed=0.04)
    assert found.inertia == pytest.approx(0.05, rel=0.01)
    assert found.fit > 0.99


def test_gyro_noise_costs_a_little_accuracy_not_the_answer():
    t, rate, asked = made_up_doublet(0.05, 0.04, noise=0.01)
    assert tuning.identify_inertia(t, rate, asked, 0.04).inertia == pytest.approx(0.05, rel=0.05)


def test_the_gains_scale_with_the_inertia_they_were_set_for():
    # my gains are per unit inertia already, so a new inertia only changes the torque they ask
    assert tuning.torque_scale(found=0.05, believed=0.04) == pytest.approx(1.25)


def made_up_roll(inertia=0.03, kf=8.5e-6, arm=0.148, dt=0.004, seconds=3.0, lag=0.02,
                 delay=0.0):  # fmt: skip
    """A drone rolling to its motors: the right pair and the left pair split by a doublet in
    their commanded speeds, the motors following those with a first-order lag, the roll rate
    integrated from their torque over the inertia."""
    t = np.arange(0.0, seconds, dt)
    split = np.where((t > 1.0) & (t < 1.2), 30.0, np.where((t > 1.2) & (t < 1.4), -30.0, 0.0))
    # PX4's quad X order: front right, back left, front left, back right (y: left positive)
    y = np.array([-arm, arm, arm, -arm])
    asked = np.stack([600.0 + split * np.sign(yy) for yy in y], axis=1)
    actual = np.empty_like(asked)
    actual[0] = asked[0]
    for k in range(1, len(t)):
        actual[k] = actual[k - 1] + (asked[k] - actual[k - 1]) * dt / lag
    torque = kf * (actual**2 * y).sum(axis=1)
    torque = np.interp(t - delay, t, torque)  # the command reaching the motors late
    rate = np.cumsum(torque / inertia) * dt
    return t, rate, asked, y


def test_the_inertia_comes_back_out_of_a_flight_log():
    t, rate, asked, y = made_up_roll(inertia=0.03)
    found = tuning.identify_roll(t, rate, asked, motor_constant=8.5e-6, rotor_y=y, lag_s=0.02)
    assert found.inertia == pytest.approx(0.03, rel=0.03)
    # without the motors' lag the torque runs ahead of the turn, and the answer is off
    rough = tuning.identify_roll(t, rate, asked, motor_constant=8.5e-6, rotor_y=y, lag_s=0.0)
    assert abs(rough.inertia / 0.03 - 1) > abs(found.inertia / 0.03 - 1)


def test_a_late_command_is_found_along_with_the_inertia():
    # the log has each command when my firmware sent it; Gazebo turns the motors a few steps
    # later, which looks like a bigger inertia if it's left out
    t, rate, asked, y = made_up_roll(inertia=0.03, delay=0.032)
    found = tuning.identify_roll_with_delay(t, rate, asked, motor_constant=8.5e-6, rotor_y=y,
                                            lag_s=0.02)  # fmt: skip
    assert found.delay_s == pytest.approx(0.032, abs=0.0041)
    assert found.inertia == pytest.approx(0.03, rel=0.03)
    on_time = tuning.identify_roll(t, rate, asked, motor_constant=8.5e-6, rotor_y=y, lag_s=0.02)
    assert on_time.inertia > 1.05 * 0.03


def test_the_doublets_give_the_inertia_with_a_trim_that_drifts():
    # three doublets, motors that speed up faster than they slow down, commands that reach
    # them 8 ms late, and a trim torque that wanders as the drone drifts (rotor drag): fitted
    # over the doublets' own windows, each with its own offset and trend
    dt, inertia, kf, arm = 0.004, 0.013, 1.58e-5, 0.1485
    t = np.arange(0.0, 9.0, dt)
    y = np.array([-arm, arm, arm, -arm])
    windows, split = [], np.zeros_like(t)
    for start in (1.0, 3.5, 6.0):
        split += np.where((t >= start) & (t < start + 0.25), 25.0, 0.0)
        split -= np.where((t >= start + 0.25) & (t < start + 0.5), 25.0, 0.0)
        windows.append((start - 0.05, start + 0.8))
    asked = np.stack([560.0 + split * np.sign(yy) for yy in y], axis=1)
    late = np.stack([np.interp(t - 0.008, t, asked[:, k]) for k in range(4)], axis=1)
    actual = tuning.lagged_asymmetric(t, late, up_s=0.0125, down_s=0.025)
    trim = 0.002 * np.sin(2 * np.pi * t / 7.0)  # a torque the fit isn't told about
    torque = kf * (actual**2 * y).sum(axis=1) + trim
    rate = np.cumsum(torque / inertia) * dt
    found = tuning.identify_roll_doublets(t, rate, asked, kf, y, windows, up_s=0.0125,
                                          down_s=0.025)  # fmt: skip
    assert found.inertia == pytest.approx(inertia, rel=0.03)
    assert found.delay_s == pytest.approx(0.008, abs=0.0041)
    assert found.fit > 0.99
