"""The parachute's opening jolt: the textbook bound, and the peak a flight's ground truth shows.
The numbers here are worked by hand."""

import numpy as np
import pytest

from pcs14.flight.drag import G
from pcs14.modules import chute


def test_the_bound_is_the_opening_force_coefficient_times_the_dynamic_pressure_and_area():
    # 12 m/s into a 1.93 m^2 canopy at sea level: q = 0.5 * 1.225 * 144 = 88.2 Pa
    force = chute.opening_force_bound(12.0, 1.93, rho=1.225)
    assert force == pytest.approx(1.7 * 88.2 * 1.93, rel=1e-3)  # about 289 N
    assert chute.opening_force_bound(24.0, 1.93, rho=1.225) == pytest.approx(4 * force)


def test_the_peak_from_a_flight_is_the_canopys_pull_on_the_drone():
    # falling at 12 m/s, then slowed to 4.6 m/s over half a second: 14.8 m/s^2 up, on top of
    # holding the drone's weight
    t = np.arange(0.0, 2.0, 0.01)
    vz = np.where(t < 1.0, -12.0, np.minimum(-12.0 + 14.8 * (t - 1.0), -4.6))
    peak = chute.peak_pull(t, vz, mass_kg=2.6, since=0.9, until=2.0)
    assert peak.force_n == pytest.approx(2.6 * (14.8 + G), rel=0.02)
    assert peak.g == pytest.approx(peak.force_n / (2.6 * G))
    assert 1.0 <= peak.at <= 1.5
    assert peak.speed_ms == pytest.approx(12.0, abs=0.2)  # how fast it fell into the opening
