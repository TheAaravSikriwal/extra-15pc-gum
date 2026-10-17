"""Hover from the thrust tables, checked by hand against the made-up 10 inch table at 24 V.

Full throttle on the 6S2P test pack (0.048 ohm): the motors want P0 = 4 x 24 V x 26.5 A
= 2544 W at 24 V, and their power scales with voltage cubed, so the pack settles where
    V = V_rest - R * P0 * V^2 / 24^3
At full charge (25.08 V rest) that's 21.134 V and 82.19 A; at the 20% reserve (21.12 V
rest) it's 18.195 V. Thrust scales with voltage squared: 2100 g x (V / 24)^2 per motor.
"""

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


def test_below_the_first_row_heads_to_zero(rotor):
    assert rotor.power_for_thrust(gf(110)) == pytest.approx(28.8 / 2)


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
