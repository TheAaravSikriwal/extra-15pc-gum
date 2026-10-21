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
    # a mark the log already has comes in once, and nothing sits before the log's start
    again = flights.playback(made_up_log(), [(12.0, "hold"), (-1.0, "early")], RESULT, "mine")
    assert [e.name for e in again.events].count("hold") == 1
    assert min(e.at for e in again.events) >= 0
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


def test_every_scenario_from_steps_4_to_7_says_what_it_tests():
    names = flights.ALL_SCENARIOS
    for name in ("hover", "payload grab", "hung flight controller", "drop from 10 m",
                 "spiral descent", "mapping run, box moved"):  # fmt: skip
        assert name in names
    assert names.index("payload grab") < names.index("chute rule") < names.index("lift")
    steps = {name: flights.about(name).step for name in names}
    assert steps["hover"] == 4 and steps["halow range"] == 6 and steps["flow run"] == 7
    for name in names:
        what = flights.about(name).what
        assert what.endswith(".") and "—" not in what  # a sentence, and no em dashes


def test_the_index_carries_the_later_steps_runs_and_what_each_tests(tmp_path):
    spiral = ScenarioResult("spiral descent", "base", True, (DRIFT,))
    moved = ScenarioResult("mapping run, box moved", "V", True, (DRIFT,))
    results = {"px4": [RESULT], "mine": [RESULT, spiral, moved]}
    flights.write_flights(tmp_path, results, lambda *_: (made_up_log(), [], RESULT))
    index = schema.Flights.model_validate_json((tmp_path / "flights.json").read_text())
    assert [r.scenario for r in index.runs if r.firmware == "mine"] == [
        "hover", "spiral descent", "mapping run, box moved"]  # fmt: skip
    files = [r.file for r in index.runs]
    assert "flights/v-mapping-run-box-moved-mine.json" in files  # no commas in a file name
    about = {a.name: a for a in index.about}
    assert about["spiral descent"].step == 7 and about["spiral descent"].what
    assert index.scenarios == list(flights.ALL_SCENARIOS)
