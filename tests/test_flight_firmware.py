"""Flying my own firmware in the flight sim: the pieces that don't need Gazebo."""

import math

import pytest

from pcs14.flight import firmware


def test_the_hover_throttle_carries_the_weight():
    info = {"mass_kg": 1.86, "motor_constant": 1.5777e-5, "top_rot_velocity": 947.0}
    throttle = firmware.hover_throttle(info)
    assert throttle * 4 * 1.5777e-5 * 947.0**2 == pytest.approx(1.86 * 9.80665)


def test_tilt_from_a_quaternion():
    assert firmware.tilt_deg(1, 0, 0, 0) == pytest.approx(0)
    half = math.radians(20) / 2
    assert firmware.tilt_deg(math.cos(half), math.sin(half), 0, 0) == pytest.approx(20)
    # a pure turn about the vertical isn't a tilt
    assert firmware.tilt_deg(math.cos(1), 0, 0, math.sin(1)) == pytest.approx(0, abs=1e-6)


def test_the_sim_layer_is_found_where_the_build_puts_it():
    found = firmware.sitl_binary({"HOME": "/home/me"})
    assert found.as_posix() == "/home/me/build/fw-sitl/sitl/pcs14_sitl"
    assert firmware.sitl_binary({"PCS14_SITL": "/x/pcs14_sitl"}).as_posix() == "/x/pcs14_sitl"
