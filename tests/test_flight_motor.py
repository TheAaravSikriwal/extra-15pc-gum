"""Gazebo's multicopter motor model, fitted to the build's motor and prop."""

import math
from pathlib import Path

import pytest

from pcs14.catalog import load_catalog
from pcs14.design import load_build, load_targets

ROOT = Path(__file__).resolve().parents[1]
G = 9.80665


def test_the_thrust_constant_by_hand():
    from pcs14.flight.motor import fit_motor_constant

    # thrust exactly k w^2 with k = 2e-5, at three speeds: the fit gives k back
    rpms = [3000.0, 6000.0, 9000.0]
    omegas = [r * 2 * math.pi / 60 for r in rpms]
    thrusts = [2e-5 * w**2 for w in omegas]
    assert fit_motor_constant(omegas, thrusts) == pytest.approx(2e-5)


def test_the_torque_constant_by_hand():
    from pcs14.flight.motor import fit_moment_constant

    # 100 W in at 80% makes 80 W on the shaft; at 1000 rad/s that's 0.08 N m, and over 5 N of
    # thrust the drag torque is 0.016 m times the thrust, the x500's own number
    assert fit_moment_constant([1000.0], [5.0], [100.0], efficiency=0.8) == pytest.approx(0.016)


@pytest.fixture(scope="module")
def mission():
    from pcs14.flight.motor import motor_model

    catalog = load_catalog(ROOT / "design" / "catalog")
    build = load_build(ROOT / "design" / "build.yaml", catalog)
    targets = load_targets(ROOT / "design" / "targets.yaml")
    setup = next(s for s in targets.combinations() if s.name == "mission")
    return build, targets, setup, motor_model(build, targets, setup, mass=2.414)


def test_four_motors_at_hover_speed_lift_mission(mission):
    _, _, _, model = mission
    lift = 4 * model.motor_constant * model.hover_rot_velocity**2
    assert lift == pytest.approx(2.414 * G, rel=0.05)


def test_the_top_speed_is_the_sizing_models_worst_case(mission):
    from pcs14.sizing.battery import Pack
    from pcs14.sizing.rotor import Rotor

    build, targets, _, model = mission
    full = Rotor.from_build(build, pessimistic=True).full_throttle(
        Pack(build.pack), targets.reserve_fraction
    )
    # at the reserve the pack itself gives a little under the 90 A cap flat out
    assert full.current <= 90.0
    # flat out, each motor makes exactly the sizing model's full-throttle thrust, at a speed
    # close to the table's own rpm for it (the motor model is a one-number fit)
    thrust = model.motor_constant * model.max_rot_velocity**2
    assert thrust == pytest.approx(full.thrust, rel=1e-9)
    assert model.max_rot_velocity == pytest.approx(full.rpm * 2 * math.pi / 60, rel=0.05)
    assert model.hover_rot_velocity < model.max_rot_velocity


def test_the_constants_land_where_a_10_inch_quad_does(mission):
    _, _, _, model = mission
    assert 5e-6 < model.motor_constant < 5e-5
    assert 0.005 < model.moment_constant < 0.04


def test_what_the_tables_cant_give_is_flagged(mission):
    _, _, _, model = mission
    assert model.rotor_drag_coefficient == pytest.approx(8.06428e-05)  # PX4's x500
    assert {"rotor_drag_coefficient", "rolling_moment_coefficient", "time_constant_up",
            "time_constant_down"} <= set(model.estimates)  # fmt: skip
