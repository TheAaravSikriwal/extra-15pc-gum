"""The companion computer's jobs against a Pi 5 and a Jetson Orin Nano: every number with its
source, and the verdict the numbers give."""

from pcs14.modules import companion


def test_every_number_has_a_source():
    for board in companion.BOARDS:
        for fact in board.facts:
            assert fact.source.startswith("http"), (board.name, fact.what)
    for job in companion.JOBS:
        assert job.source.startswith("http") or job.source.startswith("decisions.md"), job.name


def test_neither_board_encodes_video_in_hardware():
    # the live video is a CPU job on both, so it counts against the CPU on both
    assert not any(b.hardware_encoder for b in companion.BOARDS)


def test_the_pi_5_is_enough_for_the_jobs_that_stay_on_board():
    verdict = companion.verdict()
    assert verdict.pick == "Raspberry Pi 5 (4 GB)"
    assert "laptop" in verdict.why
