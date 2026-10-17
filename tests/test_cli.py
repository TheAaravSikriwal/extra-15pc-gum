"""The pcs14 command, run end to end on the made-up test catalog."""

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
    assert "Verdict: marginal" in out


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
