"""The drag plugin's math, mirrored in Python: body drag against the wind, and the parachute
opening after its ejection delay. The C++ plugin does exactly this."""

import math
from pathlib import Path

import pytest

from pcs14.flight import drag

ROOT = Path(__file__).resolve().parents[1]
RHO = drag.AIR_DENSITY


def test_drag_in_still_air_by_hand():
    force = drag.body_drag(0.015, (10.0, 0.0, 0.0), (0.0, 0.0, 0.0))
    assert force == pytest.approx((-0.5 * RHO * 0.015 * 100, 0.0, 0.0))


def test_a_headwind_on_a_drone_holding_still_pushes_it_downwind():
    # wind blowing toward -x at 5 m/s, the drone still: it gets pushed toward -x
    force = drag.body_drag(0.015, (0.0, 0.0, 0.0), (-5.0, 0.0, 0.0))
    assert force == pytest.approx((-0.5 * RHO * 0.015 * 25, 0.0, 0.0))


def test_drag_grows_with_the_square_of_speed_through_the_air():
    slow = drag.body_drag(0.015, (3.0, 4.0, 0.0), (0.0, 0.0, 0.0))  # 5 m/s
    fast = drag.body_drag(0.015, (6.0, 8.0, 0.0), (0.0, 0.0, 0.0))  # 10 m/s
    assert math.hypot(*fast) == pytest.approx(4 * math.hypot(*slow))


def test_the_canopy_sized_from_its_rating_falls_at_its_rated_speed():
    area = drag.canopy_area(rated_mass=2.5, rated_descent=4.6)
    assert area == pytest.approx(2 * 2.5 * drag.G / (RHO * 4.6**2))
    assert drag.descent_rate(area, 2.5) == pytest.approx(4.6)
    assert drag.descent_rate(area, 2.623) == pytest.approx(4.6 * math.sqrt(2.623 / 2.5))


def test_the_canopy_opens_after_the_ejection_delay():
    chute = drag.Chute(canopy_area=1.9, ejection_s=0.2, opening_s=1.0)
    assert chute.area(None) == 0.0  # not fired
    assert chute.area(0.1) == 0.0  # still leaving the tube
    assert chute.area(0.7) == pytest.approx(0.95)  # halfway open
    assert chute.area(5.0) == pytest.approx(1.9)


def test_the_harrier_carries_its_rating_and_its_timing():
    from pcs14.catalog import load_catalog

    harrier = load_catalog(ROOT / "design" / "catalog").component("fruity-chutes-harrier-40-42")
    chute = harrier.parachute
    assert chute.rated_mass_kg == 2.5 and chute.rated_descent_ms == 4.6
    assert {"ejection_s", "opening_s"} <= set(chute.estimates)
