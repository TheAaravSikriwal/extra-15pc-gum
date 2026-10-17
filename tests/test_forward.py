"""Drag and forward flight, on the made-up test build.

Mission plus the 200 g growth margin weighs 2.216 kg (21.731 N), so each motor carries
554 g (5.4328 N) in a hover, which the table says takes 85.17 W. The 10 inch prop's disk is
0.0506707 m^2, so the hover inflow is sqrt(5.4328 / (2 x 1.225 x 0.0506707)) = 6.6153 m/s.
Drag area: frame 150 + GPS 15 + V housing 60 + parachute 40 = 265 cm^2.
"""

import math

import pytest

from pcs14.sizing.drag import AIR_DENSITY, drag_area, drag_force
from pcs14.sizing.mass import mass_budget
from pcs14.sizing.rotor import CannotHover, PowerModel, Rotor
from pcs14.units import gram_force_to_newton as gf


@pytest.fixture
def mission_model(build, setups):
    budget = mass_budget(build, setups["mission"], growth_margin=0.2)
    return PowerModel(
        rotor=Rotor.from_build(build),
        weight=budget.weight,
        drag_area=drag_area(build, setups["mission"]),
        avionics_power=12.3,
    )


def test_drag_area_adds_the_frame_and_what_it_carries(build, setups):
    assert drag_area(build, setups["base"]) == pytest.approx(0.0150)
    assert drag_area(build, setups["mission"]) == pytest.approx(0.0265)


def test_drag_force():
    assert drag_force(0.0265, 10) == pytest.approx(0.5 * 1.225 * 100 * 0.0265)
    assert AIR_DENSITY == 1.225


def test_hover_inflow_and_efficiency_by_hand(mission_model):
    assert mission_model.hover_thrust == pytest.approx(gf(554), rel=1e-4)
    assert mission_model.induced_velocity(0) == pytest.approx(6.6153, abs=1e-3)
    # efficiency = 1.15 x T x v / (0.75 x P) = 1.15 x 5.4328 x 6.6153 / (0.75 x 85.17)
    assert mission_model.efficiency == pytest.approx(0.647, abs=2e-3)


def test_matches_the_hover_table_at_zero_speed(mission_model):
    assert mission_model.power(0) == pytest.approx(4 * 85.1704 + 12.3, rel=1e-4)


def test_power_dips_then_rises_with_speed(mission_model):
    speed, power = mission_model.least_power_speed()
    assert 3 < speed < 20
    assert power < mission_model.power(0)
    assert mission_model.power(25) > power


def test_inflow_falls_toward_the_fast_flight_limit(mission_model):
    # At speed, inflow tends to T / (2 rho A V)
    speed = 25
    thrust = mission_model.thrust_per_motor(speed)
    area = mission_model.rotor.prop.disk_area
    limit = thrust / (2 * AIR_DENSITY * area * speed)
    assert mission_model.induced_velocity(speed) == pytest.approx(limit, rel=0.05)


def test_tilt_balances_drag_against_weight(mission_model):
    drag = drag_force(0.0265, 15)
    assert mission_model.tilt(15) == pytest.approx(math.atan2(drag, mission_model.weight))
    assert mission_model.thrust_per_motor(15) == pytest.approx(
        math.hypot(drag, mission_model.weight) / 4
    )


def test_top_speed_is_where_thrust_or_tilt_runs_out(mission_model, build):
    from pcs14.sizing.battery import Pack

    full = mission_model.rotor.full_throttle(Pack(build.pack), soc=0.5)
    top = mission_model.top_speed(full)
    assert top > 80 / 3.6
    assert mission_model.can_fly(top, full)
    assert not mission_model.can_fly(top + 0.5, full)


def test_too_heavy_to_hover(build):
    with pytest.raises(CannotHover):
        PowerModel(rotor=Rotor.from_build(build), weight=gf(4 * 2200), drag_area=0.02)
