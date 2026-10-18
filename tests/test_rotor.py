"""Hover from the thrust tables, checked by hand against the made-up 10 inch table at 24 V.

Full throttle on the 6S2P test pack (0.048 ohm): the motors want P0 = 4 x 24 V x 26.5 A
= 2544 W at 24 V, and their power scales with voltage cubed, so the pack settles where
    V = V_rest - R * P0 * V^2 / 24^3
At full charge (25.08 V rest) that's 21.134 V and 82.19 A; at the 20% reserve (21.12 V
rest) it's 18.195 V. Thrust scales with voltage squared: 2100 g x (V / 24)^2 per motor.
"""

import dataclasses

import pytest

from pcs14.catalog import Motor, SourceKind
from pcs14.design import pick_table
from pcs14.sizing.battery import Pack
from pcs14.sizing.rotor import DERATE, Rotor
from pcs14.units import gram_force_to_newton as gf


@pytest.fixture
def rotor(build):
    return Rotor.from_build(build)


@pytest.fixture
def pack(build):
    return Pack(build.pack)


def test_power_at_a_table_row(rotor):
    assert rotor.power_for_thrust(gf(900)) == pytest.approx(24 * 6.7)


def test_power_between_rows(rotor):
    # 554 g sits 134/230 of the way from 420 g (60 W) to 650 g (103.2 W)
    assert rotor.power_for_thrust(gf(554)) == pytest.approx(60 + 134 / 230 * 43.2)


def test_below_the_first_row_power_follows_thrust_to_the_one_and_a_half(rotor):
    # Momentum theory: at a fixed prop size, power goes as thrust^1.5. Half of the first
    # row's 220 g takes 28.8 W x 0.5^1.5, not the 14.4 W a straight line would say.
    assert rotor.power_for_thrust(gf(110)) == pytest.approx(28.8 * 0.5**1.5)


def test_below_the_first_row_rpm_follows_the_square_root_of_thrust(rotor):
    # Thrust goes as rpm^2, so a quarter of the first row's thrust needs half its rpm
    assert rotor.rpm_for_thrust(gf(55)) == pytest.approx(4300 / 2)


def test_more_thrust_than_the_table_has(rotor):
    assert rotor.power_for_thrust(gf(2101)) is None


def test_rpm_at_a_thrust(rotor):
    assert rotor.rpm_for_thrust(gf(900)) == pytest.approx(8600)


def test_full_throttle_at_full_charge(rotor, pack):
    full = rotor.full_throttle(pack, soc=1.0)
    assert full.voltage == pytest.approx(21.134, abs=1e-3)
    assert full.current == pytest.approx(82.19, abs=0.01)
    assert full.thrust == pytest.approx(gf(2100 * (21.134 / 24) ** 2), rel=1e-3)
    assert full.rpm == pytest.approx(13100 * 21.134 / 24, rel=1e-3)


def test_full_throttle_at_the_reserve(rotor, pack):
    full = rotor.full_throttle(pack, soc=0.2)
    assert full.voltage == pytest.approx(18.195, abs=1e-3)
    assert full.thrust == pytest.approx(gf(2100 * (18.195 / 24) ** 2), rel=1e-3)


def test_pessimistic_data_makes_less_thrust_for_the_same_power(build, pack):
    worse = Rotor.from_build(build, pessimistic=True)
    assert DERATE[SourceKind.MANUFACTURER] == 0.10
    # 900 g pessimistic needs what 1000 g needs on the table: 160.8 + 100/250 x 69.6 W
    assert worse.power_for_thrust(gf(900)) == pytest.approx(160.8 + 0.4 * 69.6)
    assert worse.full_throttle(pack, 1.0).thrust == pytest.approx(
        0.9 * Rotor.from_build(build).full_throttle(pack, 1.0).thrust
    )


def _motor_with(tables):
    return Motor.model_validate(
        {
            "type": "motor",
            "id": "testco-two-tables",
            "maker": "Testco",
            "model": "two tables",
            "source": {"kind": "made_up", "note": "test"},
            "mass_g": 70,
            "kv": 900,
            "cells_min": 4,
            "cells_max": 6,
            "max_current_a": 40,
            "thrust_tables": tables,
        }
    )


def _table(volts, source):
    rows = [
        {"throttle_pct": 50, "thrust_g": 900, "current_a": 6.7},
        {"throttle_pct": 75, "thrust_g": 1500, "current_a": 15},
        {"throttle_pct": 100, "thrust_g": 2100, "current_a": 26.5},
    ]
    return {"prop": "testco-p10x45", "voltage_v": volts, "source": source, "rows": rows}


def test_measured_data_beats_published_data(catalog):
    stand = {"kind": "thrust_stand", "note": "bench run 1"}
    maker = {"kind": "manufacturer", "url": "https://example.com/m"}
    motor = _motor_with([_table(24, maker), _table(16, stand)])
    assert (
        pick_table(motor, catalog.prop("testco-p10x45"), 21.6).source.kind
        is SourceKind.THRUST_STAND
    )


def test_the_closest_voltage_breaks_a_tie(catalog):
    maker = {"kind": "manufacturer", "url": "https://example.com/m"}
    motor = _motor_with([_table(16, maker), _table(24, maker)])
    assert pick_table(motor, catalog.prop("testco-p10x45"), 21.6).voltage == 24


def test_a_current_cap_throttles_back_full_throttle(build, pack):
    # The firmware caps the pack at half its 90 A rating, so 45 A instead of 82 A flat out.
    # The pack sags less, and the motors get power = pack volts x 45 A, with thrust following
    # power to the 2/3 from the full-throttle row (the same law as uncapped full throttle).
    rotor = Rotor.from_build(build.variant(current_cap_fraction=0.5))
    full = rotor.full_throttle(pack, soc=1.0)
    assert full.current == 45
    assert full.voltage == pytest.approx(pack.ocv(1.0) - pack.resistance * 45)
    assert full.capped_from == pytest.approx(82.19, abs=0.01)
    share = (full.voltage * 45 / (4 * rotor.max_power)) ** (1 / 3)
    assert full.thrust == pytest.approx(rotor.max_thrust * share**2)
    assert full.rpm == pytest.approx(13100 * share)


def test_a_cap_above_the_draw_changes_nothing(build, pack):
    free = Rotor.from_build(build).full_throttle(pack, soc=1.0)
    roomy = Rotor.from_build(build.variant(current_cap_fraction=1.0))  # 90 A cap, 82 A draw
    assert roomy.full_throttle(pack, soc=1.0) == free


def test_the_cap_meets_full_throttle_without_a_jump(build, pack):
    free = Rotor.from_build(build).full_throttle(pack, soc=1.0)
    rotor = dataclasses.replace(Rotor.from_build(build), current_cap=free.current * (1 - 1e-9))
    just_under = rotor.full_throttle(pack, soc=1.0)
    assert just_under.thrust == pytest.approx(free.thrust, rel=1e-6)
    assert just_under.rpm == pytest.approx(free.rpm, rel=1e-6)
    assert just_under.voltage == pytest.approx(free.voltage, rel=1e-6)
