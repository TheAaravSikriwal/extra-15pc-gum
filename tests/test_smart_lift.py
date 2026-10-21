"""Soar mode's lift detector (#31): rising air found from the thrust it takes to hold height,
against what holding height takes in still air. Worked by hand."""

import pytest

from pcs14.smart import lift


def test_the_thrust_is_the_rotors_speeds_through_the_motor_constant():
    assert lift.thrust_n([600.0] * 4, 8.5e-6) == pytest.approx(4 * 8.5e-6 * 360000)


def test_a_thrust_deficit_in_the_sim_is_the_updraft_pushing_on_the_body():
    # 0.03 m^2 in a 4 m/s updraft: 0.5 * 1.225 * 0.03 * 16 = 0.294 N less thrust needed
    assert lift.updraft_in_sim(0.294, drag_area_m2=0.03, rho=1.225) == pytest.approx(4.0, rel=1e-3)
    assert lift.updraft_in_sim(-0.1, 0.03) == 0.0  # more thrust, not less: no lift


def test_on_a_real_rotor_rising_air_saves_the_thrust_times_its_speed():
    # momentum theory, first order: hovering in air rising at w is descending through it at w
    assert lift.power_saving_w(thrust_n=20.0, updraft_ms=1.0) == pytest.approx(20.0)


def test_lift_is_flagged_past_the_noise_in_the_averages():
    import numpy as np

    rng = np.random.default_rng(5)
    still = 18.0 + rng.normal(0, 0.6, 450)
    lifted = 17.85 + rng.normal(0, 0.6, 450)
    error = lift.standard_error(still, lifted)
    assert error == pytest.approx(0.6 * np.sqrt(2 / 450), rel=0.1)  # about 0.04 N
    assert lift.is_lift(still.mean() - lifted.mean(), error)
    assert not lift.is_lift(0.05, error)
