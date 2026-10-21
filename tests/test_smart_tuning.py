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


def made_up_roll(inertia=0.03, kf=8.5e-6, arm=0.148, dt=0.004, seconds=3.0, lag=0.02):
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
    rate = np.cumsum(torque / inertia) * dt
    return t, rate, asked, y


def test_the_inertia_comes_back_out_of_a_flight_log():
    t, rate, asked, y = made_up_roll(inertia=0.03)
    found = tuning.identify_roll(t, rate, asked, motor_constant=8.5e-6, rotor_y=y, lag_s=0.02)
    assert found.inertia == pytest.approx(0.03, rel=0.03)
    # without the motors' lag the torque runs ahead of the turn, and the answer is off
    rough = tuning.identify_roll(t, rate, asked, motor_constant=8.5e-6, rotor_y=y, lag_s=0.0)
    assert abs(rough.inertia / 0.03 - 1) > abs(found.inertia / 0.03 - 1)
