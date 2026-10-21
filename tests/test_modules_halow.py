"""HaLow as a link: the rates the radio offers, the path loss at 915 MHz with the ground's
reflection, the link budget, and how far each rate reaches. The numbers here are worked by
hand."""

import pytest

from pcs14.modules import halow


def test_the_rates_are_the_radios_on_a_2_mhz_channel():
    rates = {r.mcs: r for r in halow.RATES_2MHZ}
    assert rates[0].mbps == 0.72 and rates[0].sensitivity_dbm == -103
    assert rates[7].mbps == 7.2 and rates[7].sensitivity_dbm == -84
    assert [r.mcs for r in halow.RATES_2MHZ] == sorted(rates)


def test_free_space_loss_at_915_mhz():
    # 20 log10(1000 m) + 20 log10(915 MHz) - 147.55 = 91.68 dB
    assert halow.free_space_loss_db(1000.0) == pytest.approx(91.68, abs=0.01)


def test_past_the_breakpoint_the_ground_reflection_takes_over():
    # 30 m up, the laptop's antenna 1.5 m up: the breakpoint is 4 pi h1 h2 / lambda, 1725 m
    assert halow.breakpoint_m(30.0, 1.5) == pytest.approx(1725, rel=0.01)
    # under it, free space; past it, 40 log10(d) - 20 log10(h1 h2)
    assert halow.path_loss_db(500.0, 30.0, 1.5) == pytest.approx(halow.free_space_loss_db(500.0))
    assert halow.path_loss_db(5000.0, 30.0, 1.5) == pytest.approx(114.90, abs=0.05)


def test_the_received_power_is_the_link_budget():
    link = halow.Link()
    # 21 dBm out, 2 dBi each end, 2 dB of cables and connectors, then the path
    assert link.received_dbm(1000.0, 30.0, mcs=0) == pytest.approx(21 + 2 + 2 - 2 - 91.68, abs=0.01)


def test_each_rate_reaches_as_far_as_its_margin_allows():
    link = halow.Link()
    # MCS0 with a 10 dB fade margin: the path can lose 21 + 2 + 2 - 2 + 103 - 10 = 116 dB, past
    # the breakpoint: 10 ** ((116 + 33.06) / 40) = 5330 m
    assert link.reach_m(0, 30.0) == pytest.approx(5330, rel=0.01)
    reaches = [link.reach_m(r.mcs, 30.0) for r in halow.RATES_2MHZ]
    assert reaches == sorted(reaches, reverse=True)  # the faster, the shorter


def test_the_rate_falls_with_distance_and_never_rises():
    link = halow.Link()
    rates = [link.rate_mbps(d, 30.0) for d in (50, 200, 500, 1000, 2000, 4000, 8000)]
    assert rates[0] == 7.2
    assert rates == sorted(rates, reverse=True)
    assert rates[-1] == 0.0  # past MCS0's reach


def test_packets_drop_near_and_past_the_edge():
    link = halow.Link()
    edge = link.reach_m(0, 30.0, margin_db=0.0)
    assert link.packet_loss(edge, 30.0) == pytest.approx(0.10, abs=0.01)  # the 10% it's rated at
    assert link.packet_loss(edge / 4, 30.0) < 0.001
    assert link.packet_loss(edge * 3, 30.0) == 1.0
