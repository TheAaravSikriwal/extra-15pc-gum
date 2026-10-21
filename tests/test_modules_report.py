"""Step 6's report from made-up results: what it collects, its verdict, and what it says."""

import json

import numpy as np

from pcs14.modules import report


def result(folder, setup, scenario, passed=True, notes=None, marks=(), findings=None):
    name = f"pcs14_{setup.lower().replace('+', '_')}-{scenario.replace(' ', '-')}-mine.json"
    data = {
        "scenario": f"{scenario} (mine)",
        "setup": setup,
        "flown": True,
        "findings": findings or [{"check": "it", "passed": passed, "value": 1.0, "limit": None,
                                  "unit": "", "detail": "made up", "extra": None}],
        "note": "",
        "run": {"marks": list(marks), "notes": notes or {}},
    }  # fmt: skip
    (folder / "results").mkdir(parents=True, exist_ok=True)
    (folder / "results" / name).write_text(json.dumps(data), encoding="utf-8")


def falling_truth(start=40.0, opens=41.2, dt=0.04):
    """Hung at `start`: free fall until the canopy starts filling at `opens`, slowed to 4.4 m/s
    over the next second, then steady."""
    t = np.arange(start - 1, start + 15, dt)
    v = np.where(t < start, 0.0, 9.81 * (np.minimum(t, opens) - start))
    v = np.where(t > opens, np.maximum(v[np.searchsorted(t, opens)] - 7.4 * (t - opens), 4.4), v)
    z = 40.0 - np.cumsum(v) * dt
    return [(float(a), float(max(b, 0.05)), 0.0) for a, b in zip(t, z, strict=True)]


def made_up_exports(tmp_path):
    exports = tmp_path / "flight-sim"
    model = exports / "models" / "pcs14_p"
    model.mkdir(parents=True)
    (model / "model.json").write_text(json.dumps(
        {"mass_kg": 2.04, "chute": {"canopy_area_m2": 1.93, "ejection_s": 0.2,
                                    "opening_s": 1.0}}), encoding="utf-8")  # fmt: skip
    hung = {"hung at": 40.0, "truth": falling_truth()}
    result(exports, "P", "hung flight controller", notes=hung, marks=[[41.0, "chute fired"]])
    result(exports, "max", "drop from 10 m")
    result(exports, "base", "chute rule", passed=False)
    return exports


def test_it_collects_every_step_6_run_and_works_out_the_jolt(tmp_path):
    run = report.collect(made_up_exports(tmp_path))
    assert {(r.scenario, r.setup) for r in run.runs} == {
        ("hung flight controller", "P"),
        ("drop from 10 m", "max"),
        ("chute rule", "base"),
    }
    (jolt,) = run.jolts
    assert jolt.setup == "P" and jolt.bound_n > jolt.sim_n > 0
    assert report.verdict(run) == "fail"  # the chute rule missed


def test_the_report_says_what_it_found_and_what_it_cant_prove(tmp_path):
    run = report.collect(made_up_exports(tmp_path))
    text = report.render(run, generated="2026-10-20")
    for words in ("# Modules in sim", "## P: the parachute", "## V: vision and nav",
                  "## C: the claws", "## What it can't prove", "Raspberry Pi 5"):  # fmt: skip
        assert words in text, words
    written = report.write(made_up_exports(tmp_path / "again"), tmp_path / "out", "2026-10-20")
    names = {p.name for p in written}
    assert {"README.md", "modules.json", "opening-wide.png", "halow-wide.png"} <= names
    assert "stills/opening-wide.png" in (tmp_path / "out" / "README.md").read_text(encoding="utf-8")
    data = report.to_data(run, generated="2026-10-20")
    assert data["verdict"] == "fail" and data["unproven"]
    json.dumps(data)
