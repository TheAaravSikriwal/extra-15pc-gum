"""Wind sensing (#10) and the "turn back now" warning: the wind from how far the drone leans to
hold its position, and the energy home against it. Worked by hand."""

import math

import pytest

from pcs14.smart import wind


def test_the_lean_that_holds_still_in_a_wind_gives_that_wind():
    # 2.4 kg, 0.03 m^2 of drag area, in a 10 m/s wind from the north (blowing south): the drag
    # is 0.5 * 1.225 * 0.03 * 100 = 1.8375 N, so it leans north by atan(1.8375 / (2.4 g))
    tilt = math.atan(1.8375 / (2.4 * 9.80665))
    found = wind.from_lean(lean_north=math.sin(tilt), lean_east=0.0, mass_kg=2.4,
                           drag_area_m2=0.03, rho=1.225)  # fmt: skip
    assert found.speed_ms == pytest.approx(10.0, rel=1e-3)
    assert found.toward_north == pytest.approx(-10.0, rel=1e-3)  # blowing south
    assert found.from_deg == pytest.approx(0.0, abs=0.01)  # from the north
    assert wind.from_lean(0.0, 0.0, 2.4, 0.03).speed_ms == 0.0


def test_the_way_home_costs_more_into_the_wind():
    def power(speed):  # a made-up power curve: 300 W at hover, a little less at cruise
        return 300.0 - 2.0 * speed

    calm = wind.energy_home_wh(power, distance_m=1800.0, home_north=-1.0, home_east=0.0,
                               wind_north=0.0, wind_east=0.0, airspeed_ms=10.0)  # fmt: skip
    assert calm == pytest.approx(280.0 * 180.0 / 3600.0)  # 180 s at 280 W: 14 Wh
    headwind = wind.energy_home_wh(
        power, 1800.0, -1.0, 0.0, wind_north=5.0, wind_east=0.0, airspeed_ms=10.0
    )  # home is south, the wind blows north
    assert headwind == pytest.approx(2 * calm)  # half the ground speed, twice the time
    assert wind.energy_home_wh(power, 1800.0, -1.0, 0.0, 12.0, 0.0, 10.0) == math.inf


def test_it_says_turn_back_while_there_is_still_enough_to_get_home():
    assert not wind.turn_back(remaining_wh=80.0, reserve_wh=20.0, home_wh=30.0)
    assert wind.turn_back(remaining_wh=55.0, reserve_wh=20.0, home_wh=30.0)  # 35 < 1.25 * 30
