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


def test_a_landing_counts_where_it_was_asked_for():
    c = NS(sim=NS(failures=NS(max_touchdown_ms=1.5)))
    found = {f.check: f for f in smart.grade_landed_at(landing_at(20.0, 20.0), c, (20.0, 20.0))}
    assert found["landed where asked"].passed
    assert found["touchdown"].passed
    missed = smart.grade_landed_at(landing_at(26.0, 20.0), c, (20.0, 20.0))
    assert not next(f for f in missed if f.check == "landed where asked").passed
