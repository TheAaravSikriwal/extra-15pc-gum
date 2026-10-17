"""Streaming flights into Rerun, and the project's colors."""

import pytest

from pcs14 import style
from pcs14.sizing.battery import Pack
from pcs14.sizing.flight import fly, power_model
from pcs14.viz import Recorder


def test_colors_come_from_the_style_file():
    assert style.color("accent") == "#3DDC97"
    assert style.rgb("accent") == (0x3D, 0xDC, 0x97)
    assert style.verdict_color("pass") == style.color("accent")
    assert style.verdict_color("fail") == style.color("pop")
    assert style.verdict_color("marginal") == style.color("muted")


def test_writes_a_recording_without_a_viewer_open(build, setups, tmp_path):
    flight = fly(power_model(build, setups["mission"], 0.2), Pack(build.pack), 0, 0.2)
    path = tmp_path / "flights.rrd"
    recorder = Recorder(path=path)
    recorder.log_flight("mission", "hover", "nominal", flight, highlight=True)
    recorder.log_reserve(7200, flight.duration)
    recorder.log_summary("# Test\nMade-up parts.")
    recorder.close()
    assert path.stat().st_size > 1000


def test_needs_somewhere_to_send_the_recording():
    with pytest.raises(ValueError, match="somewhere"):
        Recorder()


def test_the_viewer_is_found_even_outside_an_activated_venv():
    from pcs14.viz.rerun_log import _viewer

    assert _viewer() is not None
