"""The spiral descent (#34): a helix on low throttle from height instead of straight down, then
straight down for the last few meters. Its geometry, worked by hand."""

import math

import numpy as np
import pytest

from pcs14.smart import spiral


def test_the_helix_sinks_at_its_rate_and_keeps_its_radius():
    s = spiral.Spiral(start_m=40.0, radius_m=8.0, sink_ms=1.5, speed_ms=4.0, straight_m=4.0)
    for t in (0.0, 5.0, 10.0):
        north, east, height = s.at(t)
        assert math.hypot(north - s.center[0], east - s.center[1]) == pytest.approx(8.0)
        assert height == pytest.approx(40.0 - 1.5 * t)
    # around the circle at 4 m/s: a turn every 2 pi 8 / 4 = 12.6 s
    assert s.lap_s == pytest.approx(2 * math.pi * 8.0 / 4.0)


def test_the_last_meters_are_straight_down_over_the_spot_it_ends_on():
    s = spiral.Spiral(start_m=40.0, radius_m=8.0, sink_ms=1.5, speed_ms=4.0, straight_m=4.0)
    turn_end = (40.0 - 4.0) / 1.5  # 24 s of spiral
    end = s.at(turn_end)
    later = s.at(turn_end + 2.0)
    assert later[:2] == pytest.approx(end[:2])  # no longer circling
    assert later[2] == pytest.approx(4.0 - 2.0 * spiral.STRAIGHT_SINK_MS)
    assert s.at(1000.0)[2] == 0.0


def test_the_grade_checks_the_radius_and_the_sink_rate():
    s = spiral.Spiral(start_m=40.0, radius_m=8.0, sink_ms=1.5, speed_ms=4.0, straight_m=4.0)
    t = np.arange(0.0, 24.0, 0.1)
    points = np.array([s.at(x) for x in t])
    found = spiral.followed(t, points[:, 0], points[:, 1], points[:, 2], s)
    assert found.radius_error_m < 0.01 and abs(found.sink_ms - 1.5) < 0.01
