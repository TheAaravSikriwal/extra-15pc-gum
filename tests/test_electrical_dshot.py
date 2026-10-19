"""DShot frames, by hand from the protocol docs, and the waveforms that drive the circuit sims."""

import pytest

from pcs14.electrical import dshot


def test_a_frame_by_hand():
    # throttle 1046, no telemetry request: 1046 << 1 = 0x82C; checksum 0x82C ^ 0x82 ^ 0x8 = ..6
    assert dshot.frame_value(1046) == 0x82C6
    assert dshot.frame_bits(1046) == [int(b) for b in f"{0x82C6:016b}"]


def test_bidirectional_frames_invert_the_checksum():
    assert dshot.frame_value(1046, bidirectional=True) == 0x82C0 | (~0x6 & 0xF)


def test_stop_is_throttle_zero():
    assert dshot.frame_value(dshot.STOP) >> 5 == 0


def test_frames_decode_back():
    for throttle in (0, 48, 1046, 2047):
        for bidi in (False, True):
            bits = dshot.frame_bits(throttle, bidirectional=bidi)
            assert dshot.decode_frame(bits, bidirectional=bidi) == throttle


def test_a_bad_checksum_doesnt_decode():
    bits = dshot.frame_bits(1046)
    bits[-1] ^= 1
    assert dshot.decode_frame(bits) is None


def test_the_waveform_times_each_bit():
    # DShot600: 1.667 us a bit, a one high for 75% of it, a zero for 37.5%
    wave = dshot.waveform([1, 0], rate=600_000, high=3.3, start=0.0, edge=1e-9)
    period = 1 / 600_000
    highs = [(t, v) for t, v in wave if v == 3.3]
    assert highs[0][0] == pytest.approx(1e-9)
    assert highs[1][0] == pytest.approx(0.75 * period, abs=2e-9)
    assert dshot.pulse_bits(wave, threshold=1.65, rate=600_000) == [1, 0]


def test_an_inverted_waveform_reads_back_the_same():
    wave = dshot.waveform([1, 0, 1, 1], rate=600_000, high=3.3, start=0.0, edge=1e-9, inverted=True)
    assert wave[0][1] == 3.3  # idle high
    assert dshot.pulse_bits(wave, threshold=1.65, rate=600_000, inverted=True) == [1, 0, 1, 1]


def test_the_rpm_reply_round_trips_through_gcr():
    # the ESC answers with a 21-bit GCR frame at 5/4 of the command rate
    for period_us in (100, 1234, 30000):
        bits = dshot.reply_bits(period_us)
        assert len(bits) == 21
        assert dshot.decode_reply(bits) == dshot.quantized_period(period_us)
