"""The project site's step pages' data (pcs14.site.steps): the README's plan, each report's
verdict and stills, and the log entries, matched to their steps."""

from pathlib import Path

from pcs14.site import schema, steps

ROOT = Path(__file__).resolve().parents[1]

PLAN = (Path(__file__).parent / "fixtures" / "site_plan.md").read_text(encoding="utf-8")


def test_the_plan_tables_rows_become_steps_with_their_links():
    rows = steps.plan_rows(PLAN)
    assert [r.name for r in rows] == ["Sizing and parts", "My firmware", "Aero (the wind tunnel)"]
    sizing = rows[0]
    assert sizing.number == "1" and sizing.status == "Done, 2026-10-17"
    assert sizing.outcome == "Emax motors. Mission hovers 25.7 min (report, log)"
    assert sizing.links[0].text == "report"
    assert sizing.links[0].url == steps.GITHUB + "docs/reports/sizing/README.md"


def test_each_log_entry_goes_to_its_step_by_its_name():
    assert steps.step_of("2026-10-17-first-real-sweep.md") == "sizing"
    assert steps.step_of("2026-10-19-electrical-report-and-weight.md") == "electrical"
    assert steps.step_of("2026-10-20-firmware-start.md") == "firmware"
    assert steps.step_of("2026-10-21-modules-in-sim.md") == "modules"
    assert steps.step_of("2026-10-21-smart-features.md") == "smart"
    assert steps.step_of("2026-10-20-wind-tunnel-hover.md") == "aero"
    assert steps.step_of("2026-10-14-plan-review.md") == "planning"


def test_the_real_steps_have_their_reports_stills_and_logs(tmp_path):
    found = steps.steps_data(ROOT / "README.md", ROOT / "docs", tmp_path)
    by_id = {s.id: s for s in found.steps}
    assert by_id["sizing"].report.verdict == "pass"
    assert any(p.endswith("flight-times.png") for p in by_id["sizing"].stills)
    # one size of each still: the wide one where there are several
    drops = [p for p in by_id["flight-sim"].stills if "drop" in p]
    assert drops == ["stills/flight-sim/drop-wide.png"]
    assert (tmp_path / "stills" / "flight-sim" / "drop-wide.png").is_file()
    assert any("first-real-sweep" in log.url for log in by_id["sizing"].logs)
    assert "1a. Talk" not in by_id  # the "in detail" rows are parts of their steps
    assert [p.name.split(".")[0] for p in by_id["firmware"].parts][:3] == ["5a", "5b", "5c"]
    assert len(found.steps) == 14  # 0 to 8, setup, and the four side tracks
    assert by_id["sizing"].logs[0].title  # the entry's own heading
    schema.Steps.model_validate(found.model_dump())
