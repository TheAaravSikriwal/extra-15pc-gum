"""The flight sim's report and data file, from a small made-up run."""

import json
from pathlib import Path

import pytest

from pcs14.design import load_targets
from pcs14.flight.grade import Finding
from pcs14.flight.report import FlightSimRun, ModelSummary, ScenarioResult, applies

ROOT = Path(__file__).resolve().parents[1]
GOLDEN = Path(__file__).parent / "fixtures" / "flight_sim" / "README.md"


def made_up_run(**changes):
    from dataclasses import replace

    setups = [s for s in load_targets(ROOT / "design" / "targets.yaml").combinations()
              if s.name in ("base", "mission")]  # fmt: skip
    models = (
        ModelSummary("base", 1675.0, 0.48, 8900, 1.55e-5, 0.0165, 120, False, 0),
        ModelSummary("mission", 2214.0, 0.58, 8930, 1.55e-5, 0.0165, 202, True, 0),
    )
    hover = (
        Finding("hover drift", True, 0.21, 0.5, "m", "drifted 0.21 m sideways over 60 s"),
        Finding("hover height", True, 0.08, 0.3, "m", "held its height within 0.08 m"),
    )
    wind = (
        Finding("wind drift", False, 1.4, 1.0, "m", "drifted 1.40 m in the wind"),
        Finding("motor headroom", True, 0.81, 0.9, "", "the busiest motor reached 81%"),
    )
    results = (
        ScenarioResult("hover", "base", True, hover),
        ScenarioResult("hover", "mission", True, hover),
        ScenarioResult("wind", "mission", True, wind),
    )
    run = FlightSimRun(
        build_label="Testco M2810 / P10x4.5 / 6S2P",
        px4="v1.17.0",
        gazebo="Harmonic",
        combinations=tuple(setups),
        models=models,
        results=results,
        estimates=("the props' drag: PX4's x500 value",),
        files=("outputs/flight-sim/models/pcs14_mission/model.sdf",),
    )
    return replace(run, **changes)


def test_the_report_matches_a_known_good_copy():
    from pcs14.flight.report import render

    assert render(made_up_run(), generated="2026-10-19") == GOLDEN.read_text(encoding="utf-8")


def test_the_verdict_follows_the_runs():
    assert made_up_run().verdict == "fail"  # the wind drift misses
    assert made_up_run(results=()).verdict == "not flown yet"


def test_each_combination_flies_only_its_scenarios():
    setups = {s.name: s for s in load_targets(ROOT / "design" / "targets.yaml").combinations()}
    assert applies("top speed", setups["mission"]) and not applies("top speed", setups["base"])
    assert applies("parachute drop", setups["P"]) and not applies("parachute drop", setups["V"])
    assert applies("payload grab", setups["max"]) and not applies("payload grab", setups["P"])
    assert applies("hover", setups["base"])


def test_the_data_file_matches_the_results():
    from pcs14.flight.report import to_data

    data = to_data(made_up_run(), generated="2026-10-19")
    assert data["verdict"] == "fail"
    wind = next(r for r in data["results"] if r["scenario"] == "wind")
    assert not wind["passed"] and wind["findings"][0]["value"] == pytest.approx(1.4)
    assert {"scenario": "parachute drop", "setup": "mission"} in data["planned"]
    json.dumps(data)


def test_the_command_generates_every_model_and_writes_the_report(tmp_path, capsys):
    from pcs14.cli import main

    out, exports = tmp_path / "report", tmp_path / "outputs"
    args = [
        "flight-sim",
        "--no-record",
        "--no-meshes",
        "--out",
        str(out),
        "--exports",
        str(exports),
    ]
    assert main(args) == 0
    assert len(list((exports / "models").glob("pcs14_*/model.sdf"))) == 8 + 1  # and the payload
    data = json.loads((out / "flight-sim.json").read_text(encoding="utf-8"))
    assert data["verdict"] == "not flown yet" and len(data["models"]) == 8
    assert "not flown yet" in capsys.readouterr().out
