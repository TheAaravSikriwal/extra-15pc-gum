"""The project site's flight playback files (pcs14.site.flights), from made-up flights."""

import json

import numpy as np
import pytest

from pcs14.flight.grade import Finding, FlightLog
from pcs14.flight.report import ScenarioResult
from pcs14.site import flights, schema


def made_up_log(seconds=60.0, rate=250.0):
    t = np.arange(0, seconds, 1 / rate)
    up = np.minimum(t, 10.0)
    position = np.column_stack([0 * t, 0.01 * t, up])
    velocity = np.gradient(position, t, axis=0)
    rotors = np.full((len(t), 4), 560.0)
    attitude = np.tile([0.0, 0.0, 0.0, 1.0], (len(t), 1))
    events = [(1.0, "armed"), (12.0, "hold"), (55.0, "landed")]
    return FlightLog(t, position, velocity, rotors, events, attitude)


DRIFT = Finding("hover drift", True, 0.01, 0.5, "m", "drifted 0.01 m")
RESULT = ScenarioResult("hover", "base", True, (DRIFT,))


def test_a_run_plays_back_at_20_hz_with_its_events_and_findings():
    p = flights.playback(made_up_log(), [(11.0, "hold start")], RESULT, "mine")
    assert p.firmware == "mine" and p.scenario == "hover" and p.passed
    assert len(p.t) == pytest.approx(60 * 20, abs=2)
    assert p.position[-1][2] == pytest.approx(10.0, abs=0.01)
    assert len(p.attitude[0]) == 4 and len(p.motors[0]) == 4
    assert [e.name for e in p.events] == ["armed", "hold start", "hold", "landed"]
    assert p.findings[0].detail == "drifted 0.01 m"


def test_a_long_run_is_thinned_so_every_file_stays_small():
    p = flights.playback(made_up_log(seconds=1800.0, rate=50.0), [], RESULT, "px4")
    assert len(p.t) <= flights.MAX_SAMPLES
    assert p.t[-1] == pytest.approx(1800.0, abs=1.0)
    text = p.model_dump_json()
    assert len(text) < 600_000  # a few hundred kilobytes, as the spec has it


def test_the_index_lists_every_run_of_both_firmwares(tmp_path):
    runs = {("px4", "base", "hover"): (made_up_log(), [], RESULT),
            ("mine", "base", "hover"): (made_up_log(), [], RESULT)}  # fmt: skip
    results = {"px4": [RESULT], "mine": [RESULT]}
    written = flights.write_flights(tmp_path, results, lambda fw, setup, scenario:
                                    runs.get((fw, setup, scenario)))  # fmt: skip
    index = schema.Flights.model_validate_json((tmp_path / "flights.json").read_text())
    assert [(r.firmware, r.file) for r in index.runs] == [
        ("px4", "flights/base-hover-px4.json"),
        ("mine", "flights/base-hover-mine.json"),
    ]
    one = json.loads((tmp_path / "flights" / "base-hover-mine.json").read_text())
    assert one["firmware"] == "mine"
    assert (tmp_path / "flights" / "base-hover-mine.js").exists()  # for pages opened from disk
    assert "flights.json" in [p.name for p in written]
