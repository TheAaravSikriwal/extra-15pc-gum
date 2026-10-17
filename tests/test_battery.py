"""The battery model, checked by hand on the made-up 6S2P test pack.

Cell: 4500 mAh, 15 milliohms, 45 A continuous, 2.5 to 4.2 V.
Pack (6S2P, plus 3 milliohms of wiring):
  capacity    2 x 4500 = 9000 mAh = 32400 C
  resistance  6 x 0.015 / 2 + 0.003 = 0.048 ohm
  max current 2 x 45 = 90 A
"""

import pytest

from pcs14.sizing.battery import Pack


@pytest.fixture
def pack(build):
    return Pack(build.pack)


def test_pack_numbers(pack):
    assert pack.capacity == pytest.approx(32400)
    assert pack.capacity_mah == pytest.approx(9000)
    assert pack.resistance == pytest.approx(0.048)
    assert pack.max_continuous_current == pytest.approx(90)
    assert pack.min_voltage == pytest.approx(15.0)


def test_resting_voltage_follows_the_cell_curve(pack):
    assert pack.ocv(1.0) == pytest.approx(6 * 4.18)
    assert pack.ocv(0.5) == pytest.approx(6 * 3.72)
    assert pack.ocv(0.25) == pytest.approx(6 * 3.555)  # halfway between 3.52 and 3.59
    assert pack.ocv(1.2) == pytest.approx(6 * 4.18)  # held at the ends
    assert pack.ocv(-0.1) == pytest.approx(6 * 3.00)


def test_voltage_sags_under_load(pack):
    assert pack.terminal_voltage(1.0, 50) == pytest.approx(25.08 - 50 * 0.048)


def test_current_for_a_power_includes_the_sag(pack):
    # Solving 0.048 I^2 - 25.08 I + 1000 = 0 by hand gives I = 43.49 A
    current = pack.current_for_power(1.0, 1000)
    assert current == pytest.approx(43.49, abs=0.01)
    assert current * pack.terminal_voltage(1.0, current) == pytest.approx(1000)


def test_asking_for_more_power_than_the_pack_can_give(pack):
    # The most this pack can ever deliver at full charge is OCV^2 / 4R = 3276 W
    assert pack.current_for_power(1.0, 3000) is not None
    assert pack.current_for_power(1.0, 3300) is None


def test_a_steady_drain_empties_at_capacity_over_current(pack):
    soc = 1.0
    for _ in range(360):
        soc = pack.drain(soc, current=9.0, seconds=10)
    assert soc == pytest.approx(0.0, abs=1e-9)  # 32400 C / 9 A = 3600 s


def test_charge_used_in_mah(pack):
    assert pack.mah_used(0.8) == pytest.approx(1800)
    assert pack.soc_at_reserve(0.20) == pytest.approx(0.20)
