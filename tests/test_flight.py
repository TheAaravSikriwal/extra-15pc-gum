"""The flight stepper: fly at a steady speed until the reserve, recording everything."""

import pytest

from pcs14.sizing.battery import Pack
from pcs14.sizing.flight import avionics_power, fly, power_model, thrust_to_weight
from pcs14.units import gram_force_to_newton as gf


@pytest.fixture
def pack(build):
    return Pack(build.pack)


@pytest.fixture
def mission(build, setups):
    return power_model(build, setups["mission"], growth_margin=0.2)


def test_avionics_power_adds_up_what_is_fitted(build, setups):
    # fc 1.0 + rx 0.5 + lidar 0.6 + safety monitor 0.7, then V: gps 0.5 + camera 1.5
    # + companion 6.0 + HaLow 2.0, and P: ejector 0.5
    assert avionics_power(build, setups["base"]) == pytest.approx(2.8)
    assert avionics_power(build, setups["mission"]) == pytest.approx(13.3)


def test_stops_at_the_reserve(mission, pack):
    flight = fly(mission, pack, speed=0, reserve_fraction=0.2)
    assert flight.ended == "reserve"
    last = flight.samples[-1]
    assert last.soc == pytest.approx(0.2)
    assert last.mah_used == pytest.approx(7200)


def test_charge_drawn_matches_what_the_pack_lost(mission, pack):
    flight = fly(mission, pack, speed=0, reserve_fraction=0.2, dt=5)
    drawn = sum(
        a.current * (b.time - a.time)
        for a, b in zip(flight.samples, flight.samples[1:], strict=False)
    )
    assert drawn == pytest.approx(0.8 * pack.capacity, rel=1e-6)


def test_steady_power_means_current_rises_as_voltage_falls(mission, pack):
    flight = fly(mission, pack, speed=0, reserve_fraction=0.2)
    first, last = flight.samples[0], flight.samples[-1]
    assert first.power == pytest.approx(last.power)
    assert last.voltage < first.voltage
    assert last.current > first.current


def test_a_gentle_cruise_outlasts_a_hover(mission, pack):
    speed, _ = mission.least_power_speed()
    hover = fly(mission, pack, speed=0, reserve_fraction=0.2)
    cruise = fly(mission, pack, speed=speed, reserve_fraction=0.2)
    assert cruise.duration > hover.duration


def test_the_step_size_barely_matters(mission, pack):
    fine = fly(mission, pack, speed=10, reserve_fraction=0.2, dt=1)
    coarse = fly(mission, pack, speed=10, reserve_fraction=0.2, dt=10)
    assert coarse.duration == pytest.approx(fine.duration, rel=0.005)


def test_thrust_to_weight_at_the_reserve_by_hand(mission, pack):
    # 4 x 2100 g x (18.195 / 24)^2 = 4 x 1207.0 g, against 2216 g
    assert thrust_to_weight(mission, pack, soc=0.2) == pytest.approx(4 * 1207.0 / 2216, rel=1e-3)


def test_headroom_is_full_throttle_thrust_over_what_is_needed(mission, pack):
    flight = fly(mission, pack, speed=0, reserve_fraction=0.2)
    assert flight.samples[0].thrust_headroom == pytest.approx(
        thrust_to_weight(mission, pack, soc=1.0)
    )


def test_too_heavy_to_hold_ends_the_flight(build, setups, pack):
    from pcs14.sizing.drag import drag_area
    from pcs14.sizing.rotor import PowerModel, Rotor

    heavy = PowerModel(
        rotor=Rotor.from_build(build),
        weight=gf(4 * 2000),
        drag_area=drag_area(build, setups["base"]),
    )
    flight = fly(heavy, pack, speed=0, reserve_fraction=0.2)
    assert flight.ended == "thrust"
