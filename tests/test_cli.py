"""The pcs14 command, run end to end on the made-up test catalog."""

import json
from pathlib import Path

from pcs14.cli import main

ROOT = Path(__file__).resolve().parents[1]
FIXTURES = Path(__file__).parent / "fixtures"
TEST_PARTS = [
    "--catalog",
    str(FIXTURES / "catalog"),
    "--build",
    str(FIXTURES / "build.yaml"),
    "--targets",
    str(ROOT / "design" / "targets.yaml"),
    "--allow-made-up",
]


def test_size_prints_every_setup_and_the_verdict(capsys):
    assert main(["size", *TEST_PARTS, "--no-record"]) == 0
    out = capsys.readouterr().out
    assert "MADE-UP TEST PARTS" in out
    for name in ("base", "V", "P", "C", "mission", "V+C", "P+C", "max"):
        assert f" {name} " in out
    assert "Verdict: pass" in out


def test_size_saves_a_recording(tmp_path):
    path = tmp_path / "size.rrd"
    assert main(["size", *TEST_PARTS, "--record", str(path)]) == 0
    assert path.stat().st_size > 10_000


def test_sweep_prints_the_ranking_with_the_winner_first(capsys):
    assert main(["sweep", *TEST_PARTS, "--no-record"]) == 0
    out = capsys.readouterr().out
    lines = [line for line in out.splitlines() if line.strip().startswith("1 ")]
    assert lines and "M2810 900KV" in lines[0]


def test_report_writes_the_whole_report(tmp_path):
    out = tmp_path / "report"
    args = ["report", *TEST_PARTS, "--out", str(out), "--no-record", "--grams", "0", "200", "100"]
    assert main(args) == 0
    assert (out / "README.md").is_file()
    assert (out / "sizing.json").is_file()
    assert len(list((out / "charts").glob("*.png"))) == 5


def test_a_made_up_report_cant_go_in_docs_reports(capsys):
    out = ROOT / "docs" / "reports" / "sizing"
    assert main(["report", *TEST_PARTS, "--out", str(out), "--no-record"]) == 2
    assert "made-up" in capsys.readouterr().err


def test_a_missing_build_file_is_a_clear_error_not_a_crash(tmp_path, capsys):
    args = ["size", *TEST_PARTS[:2], "--build", str(tmp_path / "nope.yaml"), "--allow-made-up"]
    assert main([*args, "--no-record"]) == 2
    assert "nope.yaml" in capsys.readouterr().err


def test_made_up_parts_need_the_flag(capsys):
    args = [a for a in TEST_PARTS if a != "--allow-made-up"]
    assert main(["size", *args, "--no-record"]) == 2
    assert "made up" in capsys.readouterr().err


def test_validate_runs_the_honesty_check(tmp_path, capsys):
    args = [
        "validate",
        "--catalog",
        str(FIXTURES / "catalog"),
        "--cases",
        str(FIXTURES / "validation"),
        "--cells",
        str(FIXTURES / "catalog"),
        "--out",
        str(tmp_path / "v"),
        "--allow-made-up",
    ]
    assert main(args) == 0
    assert "Testco hover test: measured 36.0 min" in capsys.readouterr().out
    assert (tmp_path / "v" / "validation.md").is_file()


def _report(tmp_path, *extra):
    build = tmp_path / "build.yaml"
    text = (FIXTURES / "build.yaml").read_text(encoding="utf-8")
    build.write_text(text.replace("parallel: 2", "parallel: 3"), encoding="utf-8")  # ranks 2nd
    out = tmp_path / "report"
    parts = [*TEST_PARTS[:3], str(build), *TEST_PARTS[4:]]
    args = ["report", *parts, "--out", str(out), "--no-record", "--grams", "0", "100", "100"]
    assert main([*args, *extra]) == 0
    return json.loads((out / "sizing.json").read_text(encoding="utf-8"))


def test_report_writes_up_the_build_file_not_the_sweeps_favorite(tmp_path):
    data = _report(tmp_path)
    assert data["build"]["pack"]["parallel"] == 3
    assert data["sweep"]["chosen_rank"] == 2


def test_report_can_write_up_the_sweeps_favorite_instead(tmp_path):
    data = _report(tmp_path, "--sweep-best")
    assert data["build"]["pack"]["parallel"] == 2
    assert data["sweep"]["chosen_rank"] == 1
