"""The Meshtastic relay (#30) as a link budget: how far two nodes reach on the ground, and how
far a node on the drone reaches. Worked by hand."""

import pytest

from pcs14.smart import relay


def test_the_presets_are_meshtastics_own():
    assert relay.PRESETS["LongFast"] == 153.0
    assert relay.PRESETS["ShortFast"] == 143.0


def test_two_nodes_on_the_ground_reach_a_few_km_over_flat_ground():
    # LongFast less a 10 dB margin: 143 dB, both 1.5 m up, past the breakpoint
    # 10 ** ((143 + 20 log10(1.5 * 1.5)) / 40) = 5640 m
    assert relay.reach_m("LongFast", 1.5, 1.5) == pytest.approx(5640, rel=0.01)


def test_a_node_in_the_air_reaches_to_the_radio_horizon():
    # 100 m up against 1.5 m: the two-ray reach is about 46 km, and so is the horizon,
    # 4.12 (sqrt 1.5 + sqrt 100) km; the shorter wins
    high = relay.reach_m("LongFast", 100.0, 1.5)
    assert high == pytest.approx(min(relay.horizon_m(100.0, 1.5), 46100), rel=0.02)
    assert relay.horizon_m(100.0, 1.5) == pytest.approx(4120 * (1.5**0.5 + 10.0), rel=1e-6)
    assert high / relay.reach_m("LongFast", 1.5, 1.5) > 7  # what the relay buys
