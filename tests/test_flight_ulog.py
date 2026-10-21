"""PX4's flight log to the graders' arrays, on made-up topics shaped the way pyulog gives them."""

import math

import numpy as np
import pytest

from pcs14.flight import ulog


def us(seconds):
    return (np.asarray(seconds) * 1e6).astype(np.uint64)


def yaw_quaternion(yaw):
    """PX4's (w, x, y, z), level and turned `yaw` rad from north toward east."""
    return np.array([math.cos(yaw / 2), 0.0, 0.0, math.sin(yaw / 2)])


def topics(seconds=10.0, rate=50.0):
    t = np.arange(0, seconds, 1 / rate) + 100.0  # PX4 booted 100 s before the flight
    n = len(t)
    climb = np.clip(t - 102.0, 0, 5)  # climbs at 1 m/s from 102 s to 5 m
    truth = {
        "timestamp": us(t),
        "x": 2.0 + 0.1 * (t - 100),  # drifting north
        "y": np.full(n, -1.0),
        "z": 0.05 - climb,  # down, starting a little under the origin
        "vx": np.full(n, 0.1),
        "vy": np.zeros(n),
        "vz": -np.where((t > 102) & (t < 107), 1.0, 0.0),
    }
    q = np.tile(yaw_quaternion(0.0), (n, 1))
    attitude = {"timestamp": us(t)} | {f"q[{k}]": q[:, k] for k in range(4)}
    te = t[::2]
    spin = np.where((te > 101) & (te < 108), 600.0, 0.0)
    esc = {"timestamp": us(te)} | {f"esc[{k}].esc_rpm": spin for k in range(4)}
    ts = np.array([100.0, 101.0, 102.0, 107.5, 108.5])
    status = {
        "timestamp": us(ts),
        "arming_state": np.array([1, 2, 2, 2, 1]),
        "nav_state": np.array([2, 2, 17, 18, 18]),
    }
    land = {"timestamp": us([100.0, 102.2, 107.8]), "landed": np.array([True, False, True])}
    flags = {
        "timestamp": us([100.0, 104.0, 105.0]),
        "gcs_connection_lost": np.array([False, True, True]),
        "battery_warning": np.array([0, 0, 1]),
    }
    imu_t = np.arange(0, seconds, 1 / 250) + 100.0
    imu = {"timestamp": us(imu_t)}
    imu |= {f"accelerometer_m_s2[{k}]": np.full(len(imu_t), [0, 0, -9.8][k]) for k in range(3)}
    imu |= {f"gyro_rad[{k}]": np.zeros(len(imu_t)) for k in range(3)}
    return {
        "vehicle_local_position_groundtruth": truth,
        "vehicle_attitude_groundtruth": attitude,
        "esc_status": esc,
        "vehicle_status": status,
        "vehicle_land_detected": land,
        "failsafe_flags": flags,
        "sensor_combined": imu,
    }


def test_the_ground_truth_turns_to_east_north_up_from_the_start():
    log = ulog.flight_log(topics())
    assert log.t[0] == pytest.approx(100.0)
    # east is PX4's y, north its x, and the height is measured from where it started
    assert log.position[0] == pytest.approx([-1.0, 2.0, 0.0])
    assert log.position[-1, 2] == pytest.approx(5.0)
    assert log.velocity[0] == pytest.approx([0.0, 0.1, 0.0])
    k = np.searchsorted(log.t, 104.0)
    assert log.velocity[k, 2] == pytest.approx(1.0)  # climbing is up


def test_the_attitude_turns_to_forward_left_up_and_east_north_up():
    # level and facing north in PX4's frames is a quarter turn left of east in ours
    q = ulog.enu_attitude(yaw_quaternion(0.0))
    assert np.abs(q) == pytest.approx([0, 0, math.sqrt(0.5), math.sqrt(0.5)])
    assert q[2] * q[3] > 0  # +90 degrees about up, not -90
    # facing east is no turn at all
    assert np.abs(ulog.enu_attitude(yaw_quaternion(math.pi / 2))) == pytest.approx([0, 0, 0, 1])


def test_tilt_ignores_heading():
    pitched = np.array([math.cos(0.25), 0.0, math.sin(0.25), 0.0])  # 0.5 rad nose up
    turned = ulog._multiply(yaw_quaternion(1.2), pitched)
    assert ulog.tilt(pitched) == pytest.approx(0.5)
    assert ulog.tilt(turned) == pytest.approx(0.5)
    assert ulog.tilt(yaw_quaternion(2.0)) == pytest.approx(0.0, abs=1e-7)


def euler_quaternion(roll, pitch, yaw):
    """PX4's (w, x, y, z) for those angles, turned z then y then x."""
    cr, sr = math.cos(roll / 2), math.sin(roll / 2)
    cp, sp = math.cos(pitch / 2), math.sin(pitch / 2)
    cy, sy = math.cos(yaw / 2), math.sin(yaw / 2)
    return np.array([
        cr * cp * cy + sr * sp * sy,
        sr * cp * cy - cr * sp * sy,
        cr * sp * cy + sr * cp * sy,
        cr * cp * sy - sr * sp * cy,
    ])  # fmt: skip


def test_px4s_angles_come_back_out_of_our_frames():
    for angles in [(0.2, 0.0, 0.0), (0.0, -0.3, 0.0), (0.1, 0.25, 2.0), (-0.4, 0.1, -1.0)]:
        ours = ulog.enu_attitude(euler_quaternion(*angles))
        assert ulog.px4_euler(ours) == pytest.approx(angles, abs=1e-9)


def test_rotor_speeds_follow_the_escs():
    log = ulog.flight_log(topics())
    k = np.searchsorted(log.t, 104.0)
    assert log.rotor_speed[k] == pytest.approx([600.0] * 4)
    assert log.rotor_speed[0] == pytest.approx([0.0] * 4)


def test_the_events_in_order():
    log = ulog.flight_log(topics(), marks=[(103.0, "hover")])
    names = [n for _, n in log.events]
    assert names[:2] == ["position", "armed"]
    for earlier, later in [
        ("takeoff", "took off"),
        ("took off", "hover"),
        ("hover", "link lost"),
        ("link lost", "low battery"),
        ("low battery", "land"),
        ("land", "landed"),
        ("landed", "motors stopped"),
        ("motors stopped", "disarmed"),
    ]:
        assert log.when(earlier) < log.when(later), (earlier, later)
    assert log.when("motors stopped") == pytest.approx(108.0, abs=0.05)


def test_a_flight_that_never_spins_never_stops():
    found = ulog.events({}, t=np.arange(3.0), rotor_speed=np.zeros((3, 4)))
    assert found == []


def test_the_imu_samples_carry_the_tilt():
    made_up = topics(seconds=1.0)
    samples = ulog.imu_samples(made_up)
    assert len(samples) == len(made_up["sensor_combined"]["timestamp"])
    assert samples[0].accel == pytest.approx((0, 0, -9.8))
    assert samples[0].tilt == pytest.approx(0.0, abs=1e-7)
    assert samples[0].t == pytest.approx(100.0)


def test_a_healthy_trace_fires_no_triggers(targets):
    from pcs14.safety.triggers import triggers

    assert triggers(ulog.imu_samples(topics()), targets.flight_sim.triggers) == []


def test_a_failsafe_already_up_at_boot_isnt_an_event():
    made_up = topics()
    made_up["failsafe_flags"]["gcs_connection_lost"] = np.array([True, False, True])
    names = [n for _, n in ulog.flight_log(made_up).events]
    assert names.count("link lost") == 1  # only the real one, at 105 s
    assert ulog.flight_log(made_up).when("link lost") == pytest.approx(105.0)


def test_the_motors_commands_are_kept_at_their_own_rate_too():
    # the ground truth can be slower than the motors (50 Hz against 250 in my firmware's
    # logs); self-tuning needs every command, not the ones nearest the truth's samples
    made_up = topics()
    te = np.arange(0, 10.0, 1 / 250) + 100.0
    made_up["esc_status"] = {"timestamp": us(te)} | {
        f"esc[{k}].esc_rpm": 600.0 + 10.0 * np.sin(2 * np.pi * 30.0 * te) for k in range(4)
    }
    log = ulog.flight_log(made_up)
    t, speeds = log.esc
    assert len(t) == len(te) and speeds.shape == (len(te), 4)
    assert speeds[:, 0].max() - speeds[:, 0].min() == pytest.approx(20.0, abs=0.5)
