"""The safety monitor's switch in ngspice: DShot passing with the Teensy on, off and cutting, the
takeover, the listening lines, and the receiver's line. Skipped without ngspice."""

from pathlib import Path

import pytest

from pcs14.electrical import tools
from pcs14.electrical.spice import signals, switch

ROOT = Path(__file__).resolve().parents[1]
pytestmark = pytest.mark.skipif(tools.find("ngspice") is None, reason="ngspice isn't installed")


def test_decoding_frames_from_a_made_up_waveform():
    from pcs14.electrical import dshot

    wave = []
    for start in (2e-6, 100e-6):
        bits = dshot.frame_bits(1046, bidirectional=True)
        wave += dshot.waveform(bits, rate=600_000, high=3.3, start=start, edge=2e-9, inverted=True)
    times = [t for t, _ in wave]
    volts = [v for _, v in wave]
    assert signals.frames(times, volts, inverted=True) == [1046, 1046]


@pytest.fixture(scope="module")
def runs(tmp_path_factory):
    return switch.run_all(switch.Wiring.from_design(ROOT), tmp_path_factory.mktemp("switch"))


def test_the_flight_controller_drives_the_esc_with_the_teensy_on(runs):
    run = runs["Teensy on"]
    assert run.esc_frames == [switch.THROTTLE, switch.THROTTLE]
    assert run.fc_replies == [switch.reply_period(), switch.reply_period()]
    assert run.passed, [f.detail for f in run.findings if not f.passed]


def test_nothing_changes_with_the_teensy_unpowered(runs):
    run = runs["Teensy off"]
    assert run.esc_frames == [switch.THROTTLE, switch.THROTTLE]
    assert run.fc_replies == [switch.reply_period(), switch.reply_period()]
    assert run.passed, [f.detail for f in run.findings if not f.passed]


def test_cutting_hands_the_esc_stop_frames(runs):
    run = runs["Cutting"]
    assert run.esc_frames == [0, 0]
    assert run.passed, [f.detail for f in run.findings if not f.passed]


def test_the_takeover_costs_at_most_one_frame(runs):
    run = runs["Takeover"]
    assert set(run.esc_frames) <= {switch.THROTTLE, 0, None}
    assert run.esc_frames.count(None) <= 1
    assert run.esc_frames[0] == switch.THROTTLE and run.esc_frames[-1] == 0
    assert run.passed, [f.detail for f in run.findings if not f.passed]


def test_without_the_buffers_a_dead_teensy_drags_the_line_down(runs):
    run = runs["No buffers, Teensy off"]
    assert not run.passed  # on purpose: this is why the buffers are there
    assert run.esc_frames != [switch.THROTTLE, switch.THROTTLE]


def test_the_receiver_line_is_fine_with_the_teensy_off(runs):
    run = runs["Receiver, Teensy off"]
    assert run.passed, [f.detail for f in run.findings if not f.passed]
