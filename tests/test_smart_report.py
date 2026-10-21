"""Step 7's report: from the flight sim's results to docs/reports/smart/, on made-up results."""

import json

from pcs14.smart import report


def result(tmp, scenario, setup, findings, notes=None):
    folder = tmp / "results"
    folder.mkdir(parents=True, exist_ok=True)
    name = f"pcs14_{setup.lower()}-{scenario.replace(' ', '-')}-mine.json"
    data = {
        "scenario": scenario, "setup": setup, "flown": True,
        "findings": [{"check": c, "passed": ok, "value": None, "limit": None, "unit": "",
                      "detail": d, "extra": None} for c, ok, d in findings],
        "run": {"notes": notes or {}, "marks": []},
    }  # fmt: skip
    (folder / name).write_text(json.dumps(data), encoding="utf-8")


DOUBLET = ("roll inertia", True, "found 0.01292 kg m^2 against the model's 0.01293: -0.1% "
           "(fit 1.00, the motors 8 ms late)")  # fmt: skip


def detection(found_ok=True):
    shed = {"label": "shed", "left": 0, "top": 0, "right": 100, "bottom": 100}
    near = {"label": "brown cube", "left": 5, "top": 5, "right": 100, "bottom": 100}
    far = {"label": "person", "left": 600, "top": 600, "right": 620, "bottom": 620}
    return {"model": "qwen2.5vl:7b", "prompt": "every object, in JSON",
            "frames": [{"frame": 1, "t": 1.0, "north_m": 0.0, "truth": [shed],
                        "found": [near] if found_ok else [far]}]}  # fmt: skip


def test_the_tuning_table_comes_back_out_of_the_findings(tmp_path):
    result(tmp_path, "roll doublet", "base", [DOUBLET])
    rows = report.tuning_rows(report.collect_runs(tmp_path))
    assert rows == [("base", 0.01292, 0.01293, 1.0, 0.008)]


def test_the_verdict_needs_every_run_and_the_detection(tmp_path):
    result(tmp_path, "roll doublet", "base", [DOUBLET])
    result(tmp_path, "steps", "base", [("step settling", False, "slow")])  # step 4's: not here
    runs = report.collect_runs(tmp_path)
    assert [r.scenario for r in runs] == ["roll doublet"]
    assert report.verdict(runs, None) == "pass"
    assert report.verdict(runs, detection()) == "pass"
    assert report.verdict(runs, detection(found_ok=False)) == "fail"
    assert report.verdict([], None) == "not run"


def test_the_report_is_written_with_what_there_is(tmp_path):
    exports = tmp_path / "flight-sim"
    result(exports, "roll doublet", "base", [DOUBLET])
    smart = tmp_path / "smart"
    smart.mkdir()
    (smart / "detect.json").write_text(json.dumps(detection()), encoding="utf-8")
    out = tmp_path / "reports"
    written = report.write(exports, out, "2026-10-21", run_model=False)
    text = (out / "README.md").read_text(encoding="utf-8")
    assert "**pass.**" in text and "| base | 0.01292 kg m² |" in text
    assert "1 of 1 true things" in text  # the detection's own numbers
    data = json.loads((out / "smart.json").read_text(encoding="utf-8"))
    assert data["verdict"] == "pass" and data["tuning"][0]["setup"] == "base"
    assert (out / "stills" / "tuning-wide.png") in written
    assert not any("flow" in p.name for p in written)  # no flow run here, so no still
