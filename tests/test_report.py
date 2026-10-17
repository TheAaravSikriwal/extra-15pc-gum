"""The sizing report: Markdown, charts in the project's look, and the data file."""

import json
import struct
from pathlib import Path

import pytest

from pcs14.catalog import load_catalog
from pcs14.design import load_build, load_targets
from pcs14.report import fmt_value, write_report
from pcs14.sizing.checks import evaluate
from pcs14.sizing.sweep import margin_curve, sweep

ROOT = Path(__file__).resolve().parents[1]
FIXTURES = Path(__file__).parent / "fixtures"
GOLDEN = FIXTURES / "report" / "README.md"


@pytest.fixture(scope="module")
def results():
    catalog = load_catalog(FIXTURES / "catalog", allow_made_up=True)
    build = load_build(FIXTURES / "build.yaml", catalog)
    targets = load_targets(ROOT / "design" / "targets.yaml")
    design = evaluate(build, targets)
    return {
        "design": design,
        "sweep": sweep(build, catalog, targets),
        "margin": margin_curve(build, targets, grams=range(0, 401, 100)),
    }


@pytest.fixture(scope="module")
def report(results, tmp_path_factory):
    out = tmp_path_factory.mktemp("report")
    write_report(out, **results, made_up=True, generated="2026-10-17")
    return out


@pytest.mark.parametrize(
    ("value", "unit", "higher", "shown"),
    [
        (1.9998, ":1", True, "1.99"),  # never shows a fail as meeting the limit
        (2.004, ":1", True, "2.00"),
        (1.15, ":1", True, "1.15"),
        (90.01, "A", False, "90.1"),
        (89.96, "A", False, "90.0"),
        (27.06, "min", True, "27.0"),
    ],
)
def test_rounding_goes_toward_failing(value, unit, higher, shown):
    assert fmt_value(value, unit, higher) == shown


def test_the_report_matches_a_known_good_copy(report):
    assert (report / "README.md").read_text(encoding="utf-8") == GOLDEN.read_text(encoding="utf-8")


def test_a_made_up_report_says_so_up_front(report):
    head = (report / "README.md").read_text(encoding="utf-8")[:600]
    assert "made-up test parts" in head


def test_charts_come_out_at_the_post_size(report):
    charts = sorted((report / "charts").glob("*.png"))
    assert [c.stem for c in charts] == ["battery", "flight-times", "margin", "power", "sweep"]
    for chart in charts:
        width, height = struct.unpack(">II", chart.read_bytes()[16:24])
        assert (width, height) == (1080, 1350), chart.name


def test_the_data_file_matches_the_results(report, results):
    data = json.loads((report / "sizing.json").read_text(encoding="utf-8"))
    design = results["design"]
    assert data["made_up"] is True
    assert data["verdict"] == design.verdict
    mission = next(s for s in data["setups"] if s["name"] == "mission")
    assert mission["mass_g"] == pytest.approx(2216)
    tw = next(c for c in mission["checks"] if c["name"] == "Thrust-to-weight at the reserve")
    assert tw["nominal"] == pytest.approx(design.setup("mission").check(tw["name"]).nominal)
    assert len(mission["flights"]["cruise/nominal"]["time_s"]) <= 200
    assert data["sweep"]["ranked"][0]["motor"] == "testco-m2810-900kv"


def test_made_up_reports_cant_go_in_docs_reports(results):
    with pytest.raises(ValueError, match="made-up"):
        write_report(ROOT / "docs" / "reports" / "sizing", **results, made_up=True)
