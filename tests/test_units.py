"""Unit conversions, checked against numbers worked out by hand."""

import pytest

from pcs14 import units


def test_standard_gravity():
    assert units.G0 == 9.80665


@pytest.mark.parametrize(
    ("convert", "value", "expected"),
    [
        (units.g_to_kg, 250, 0.25),
        (units.kg_to_g, 2.5, 2500),
        (units.mm_to_m, 450, 0.45),
        (units.m_to_mm, 0.254, 254),
        (units.inch_to_m, 10, 0.254),
        (units.m_to_inch, 0.2286, 9),
        (units.mah_to_coulomb, 4500, 16200),  # 4.5 Ah is 4.5 A for 3600 s
        (units.coulomb_to_mah, 32400, 9000),
        (units.kmh_to_ms, 80, 22.2222222),
        (units.ms_to_kmh, 10, 36),
        (units.gram_force_to_newton, 1000, 9.80665),
        (units.newton_to_gram_force, 19.6133, 2000),
        (units.mohm_to_ohm, 15, 0.015),
        (units.cm2_to_m2, 400, 0.04),
        (units.seconds_to_minutes, 1800, 30),
        (units.minutes_to_seconds, 25, 1500),
    ],
)
def test_conversion(convert, value, expected):
    assert convert(value) == pytest.approx(expected, rel=1e-6)


@pytest.mark.parametrize(
    ("there", "back"),
    [
        (units.g_to_kg, units.kg_to_g),
        (units.mm_to_m, units.m_to_mm),
        (units.inch_to_m, units.m_to_inch),
        (units.mah_to_coulomb, units.coulomb_to_mah),
        (units.kmh_to_ms, units.ms_to_kmh),
        (units.gram_force_to_newton, units.newton_to_gram_force),
        (units.seconds_to_minutes, units.minutes_to_seconds),
    ],
)
def test_round_trip(there, back):
    assert back(there(123.456)) == pytest.approx(123.456, rel=1e-12)
