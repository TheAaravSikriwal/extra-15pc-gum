"""Step 7's scenarios without Gazebo: where they fly, and their graders on made-up flights."""

from types import SimpleNamespace as NS

import numpy as np

from pcs14.flight import report
from pcs14.flight.grade import FlightLog
from pcs14.flight.scenarios import scenarios, smart


def setup(name, modules=()):
    return NS(name=name, modules=modules, min_top_speed=None, hold_position_in_wind=None)


def landing_at(east, north, t_end=30.0):
    t = np.arange(0.0, t_end, 0.1)
    z = np.clip(15.0 - np.maximum(t - 20.0, 0) * 1.5, 0.07, 15.0)
    pos = np.stack([np.full_like(t, east), np.full_like(t, north), z], axis=1)
    vel = np.gradient(pos, t, axis=0)
    return FlightLog(t=t, position=pos, velocity=vel, rotor_speed=np.zeros((len(t), 4)),
                     events=[(28.0, "landed")])  # fmt: skip


def test_the_landing_modes_fly_in_base_and_stay_out_of_step_4s_matrix():
    assert report.applies("turn back", setup("V", ("V",)))
    assert report.applies("planned mission", setup("mission", ("V", "P")))
    assert report.applies("spiral descent", setup("base"))
    assert report.applies("lift", setup("base"))
    assert not report.applies("planned mission", setup("V", ("V",)))
    assert not report.applies("turn back", setup("base"))
    for name in smart.LANDING:
        assert name in scenarios() and name not in report.SCENARIOS
        assert report.applies(name, setup("base"))
        assert not report.applies(name, setup("V", ("V",)))  # the modes aren't a module's


def test_the_wind_from_a_hover_log_is_the_lean_turned_into_a_speed():
    import math

    # 2 kg, 0.02 m^2, a 6 m/s wind toward the north: drag 0.441 N, so it leans south... into
    # the wind, which comes from the south: its thrust axis tips toward the south
    tilt = math.atan(0.5 * 1.225 * 0.02 * 36 / (2.0 * 9.80665))
    t = np.arange(0.0, 20.0, 0.1)
    q = np.tile([math.sin(tilt / 2), 0.0, 0.0, math.cos(tilt / 2)], (len(t), 1))  # about east
    log = FlightLog(t=t, position=np.zeros((len(t), 3)), velocity=np.zeros((len(t), 3)),
                    rotor_speed=np.zeros((len(t), 4)), attitude=q)  # fmt: skip
    found = smart.wind_from_log(log, 5.0, 15.0, mass_kg=2.0, drag_area_m2=0.02)
    assert abs(found.speed_ms - 6.0) < 0.01
    assert abs(found.toward_north - 6.0) < 0.01  # blowing north


def test_the_way_home_is_graded_against_the_flights_own_power():
    # 4 Wh measured on the way home; a prediction of 4.4 Wh is 10% off, on the safe side
    found = smart.grade_prediction(predicted_wh=4.4, measured_wh=4.0)
    assert found.passed and abs(found.value - 0.10) < 0.01
    assert not smart.grade_prediction(predicted_wh=8.0, measured_wh=4.0).passed
    # a little optimistic is what the warning's 1.25x margin is for; more than that isn't
    assert smart.grade_prediction(predicted_wh=3.5, measured_wh=4.0).passed
    assert not smart.grade_prediction(predicted_wh=3.0, measured_wh=4.0).passed


def test_the_gauge_energy_integrates_volts_times_amps():
    samples = [(t, 24.0, 10.0) for t in np.arange(100.0, 160.0, 0.5)]
    assert abs(smart.gauge_wh(samples, 100.0, 160.0) - 240.0 * 59.5 / 3600) < 1e-9


def test_a_planned_mission_counts_each_waypoint_it_got_to():
    from pcs14.smart import missions

    plan = missions.Plan(name="made up", end="return", waypoints=[
        missions.Waypoint(north_m=30, east_m=0, height_m=15),
        missions.Waypoint(north_m=30, east_m=20, height_m=15)])  # fmt: skip
    t = np.arange(0.0, 60.0, 0.1)
    # out to the first point, across to the second, and home (east, north, up)
    east = np.interp(t, [0, 10, 20, 30, 40, 50, 60], [0, 0, 0, 20, 20, 0, 0])
    north = np.interp(t, [0, 10, 20, 30, 40, 50, 60], [0, 0, 30, 30, 30, 0, 0])
    up = np.interp(t, [0, 10, 50, 58, 60], [0, 15, 15, 0.07, 0.07])
    pos = np.stack([east, north, up], axis=1)
    log = FlightLog(t=t, position=pos, velocity=np.gradient(pos, t, axis=0),
                    rotor_speed=np.zeros((len(t), 4)), events=[(59.0, "landed")])  # fmt: skip
    found = smart.grade_waypoints(log, plan)
    assert [f.passed for f in found] == [True, True]
    plan.waypoints[1].east_m = 35  # never went there
    assert not smart.grade_waypoints(log, plan)[1].passed


def test_the_lift_grade_finds_the_column_by_the_thrust_it_saves():
    t = np.arange(0.0, 60.0, 0.1)
    # 580 rad/s holding still, a little less in the rising air: what a 4 m/s updraft takes off
    # a body of 0.03 m^2 (0.294 N), with the hover's wobble on top
    rng = np.random.default_rng(6)
    less = 580.0 * (1 - 0.294 / (4 * 8.5e-6 * 580.0**2)) ** 0.5
    speed = np.where((t > 30) & (t < 45), less, 580.0) + rng.normal(0, 2.0, len(t))
    log = FlightLog(t=t, position=np.zeros((len(t), 3)), velocity=np.zeros((len(t), 3)),
                    rotor_speed=np.tile(speed[:, None], (1, 4)),
                    events=[(10.0, "still start"), (22.0, "still end"),
                            (32.0, "lifted start"), (44.0, "lifted end")])  # fmt: skip
    c = NS(model={"motor_constant": 8.5e-6, "drag_area_m2": 0.03})
    found = {f.check: f for f in smart.grade_lift(log, None, c)}
    assert found["lift found"].passed
    assert found["the updraft"].passed


def test_a_landing_counts_where_it_was_asked_for():
    c = NS(sim=NS(failures=NS(max_touchdown_ms=1.5)))
    found = {f.check: f for f in smart.grade_landed_at(landing_at(20.0, 20.0), c, (20.0, 20.0))}
    assert found["landed where asked"].passed
    assert found["touchdown"].passed
    missed = smart.grade_landed_at(landing_at(26.0, 20.0), c, (20.0, 20.0))
    assert not next(f for f in missed if f.check == "landed where asked").passed
