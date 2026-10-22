"""The project site's step pages' data (pcs14.site.steps): the README's plan, each report as it
stands now, its stills, and the log entries, matched to their steps."""

import json
from pathlib import Path

from pcs14.site import schema, steps

ROOT = Path(__file__).resolve().parents[1]

PLAN = (Path(__file__).parent / "fixtures" / "site_plan.md").read_text(encoding="utf-8")
LIBRARY = frozenset({"docs/reports/sizing/README.md", "docs/reports/flight-sim/README.md",
                     "docs/log/2026-10-17-first-real-sweep.md"})  # fmt: skip


def test_the_plan_tables_rows_become_steps_with_their_links():
    rows = steps.plan_rows(PLAN, LIBRARY)
    assert [r.name for r in rows] == ["Sizing and parts", "My firmware", "Aero (the wind tunnel)"]
    sizing = rows[0]
    assert sizing.number == "1" and sizing.status == "Done, 2026-10-17"
    # the links are listed apart, so the parenthesis of them leaves the words
    assert sizing.outcome == "Emax motors. Mission hovers 25.7 min"
    assert sizing.links[0].text == "report"
    assert sizing.links[0].url == "#/library/docs/reports/sizing/README"  # in the library
    firmware = rows[1]
    assert firmware.outcome == "C++17, the same runs as PX4's"  # a link in the words keeps them
    assert (
        firmware.links[0].url
        == "#/library/docs/reports/flight-sim/README~my-firmware-the-same-scenarios"
    )
    assert firmware.links[1].url == steps.GITHUB + "docs/plans/2026-10-20-firmware.md"  # not in it


def test_a_side_track_has_its_purpose_and_when_it_starts():
    aero = steps.plan_rows(PLAN)[2]
    assert aero.side_track and aero.purpose == "The virtual wind tunnel"
    assert aero.starts_after == "Step 2" and aero.status == "In progress"
    # a label used twice gets its file's date
    assert [link.text for link in aero.links] == ["log, 2026-10-20", "log, 2026-10-22"]


def test_the_in_detail_rows_keep_what_happens_and_their_links():
    (talk,) = steps.detail_rows(PLAN)
    assert talk.step == "1" and talk.what == "Settle the power math"
    assert talk.outcome == "Eight questions settled"
    assert talk.links[0].text == "log"


def test_each_log_entry_goes_to_its_step_by_its_name():
    assert steps.step_of("2026-10-17-first-real-sweep.md") == "sizing"
    assert steps.step_of("2026-10-19-electrical-report-and-weight.md") == "electrical"
    assert steps.step_of("2026-10-20-firmware-start.md") == "firmware"
    assert steps.step_of("2026-10-21-modules-in-sim.md") == "modules"
    assert steps.step_of("2026-10-21-smart-features.md") == "smart"
    assert steps.step_of("2026-10-20-wind-tunnel-hover.md") == "aero"
    assert steps.step_of("2026-10-14-plan-review.md") == "planning"
    assert steps.step_of("2026-10-14-moving-to-the-pc.md") == "setup"
    assert steps.step_of("2026-10-21-the-drone-view.md") == "site"
    assert steps.step_of("2026-10-30-something-else.md") is None  # not quietly planning's


def test_every_real_log_entry_has_a_step():
    for f in (ROOT / "docs" / "log").glob("*.md"):
        assert steps.step_of(f.name), f.name


def test_a_reports_verdict_comes_in_its_own_words():
    text = "\n".join([
        "# R", "", "*Generated today.*", "", "## The verdict", "",
        "**Pass.** All 4 [checks](x.md) pass.", "Built from `a` parts.", "",
        "![a picture](p.png)", "", "| a | b |", "", "## Next", "", "Not this.", "",
    ])  # fmt: skip
    assert steps.says(text, "The verdict") == ["Pass. All 4 checks pass. Built from a parts."]
    assert steps.says("# Pack\n\n*Generated today.*\n\nNothing built.\n\n## Costs\n", None) == [
        "Nothing built."
    ]
    found = steps.sections(text, "docs/reports/r/README", "The verdict")
    assert [s.text for s in found] == ["The verdict", "Next"]
    assert found[1].url == "#/library/docs/reports/r/README~next"


def test_the_real_steps_have_their_reports_stills_and_logs(tmp_path):
    found = steps.steps_data(ROOT / "README.md", ROOT / "docs", tmp_path)
    by_id = {s.id: s for s in found.steps}
    assert by_id["sizing"].report.verdict == "pass"
    assert by_id["sizing"].report.url == "#/library/docs/reports/sizing/README"
    assert any(p.endswith("flight-times.png") for p in by_id["sizing"].stills)
    # one size of each still: the wide one where there are several
    drops = [p for p in by_id["flight-sim"].stills if "drop" in p]
    assert drops == ["stills/flight-sim/drop-wide.png"]
    assert (tmp_path / "stills" / "flight-sim" / "drop-wide.png").is_file()
    assert any("first-real-sweep" in log.url for log in by_id["sizing"].logs)
    assert all(log.url.startswith("#/library/docs/log/") for s in found.steps for log in s.logs)
    assert "1a. Talk" not in by_id  # the "in detail" rows are parts of their steps
    assert [p.name.split(".")[0] for p in by_id["firmware"].parts][:3] == ["5a", "5b", "5c"]
    assert all(p.what for s in found.steps for p in s.parts)
    assert len(found.steps) == 14  # 0 to 8, setup, and the four side tracks
    assert by_id["sizing"].logs[0].title and not by_id["sizing"].logs[0].title.startswith("2026")
    assert by_id["setup"].logs, "setup has its own log entries"
    assert by_id["structure"].purpose and by_id["structure"].starts_after == "Step 2"
    assert by_id["aero"].learning[-1].url.startswith("#/library/docs/learning~19-")
    # every link that's a doc in the library stays on the site
    for s in found.steps:
        for link in s.links + [link for p in s.parts for link in p.links]:
            assert link.url.startswith(("#/library/", "https://github.com/")), link.url
            if link.url.startswith("https://github.com/"):
                assert not link.url.endswith(".md"), link.url
        assert len({link.text for link in s.links}) == len(s.links), s.id
    schema.Steps.model_validate(found.model_dump())


def _report(name: str) -> tuple[dict, str]:
    folder = ROOT / "docs" / "reports" / name
    return (json.loads((folder / f"{name}.json").read_text(encoding="utf-8")),
            (folder / "README.md").read_text(encoding="utf-8"))  # fmt: skip


def test_each_reports_numbers_now_agree_with_the_report(tmp_path):
    found = {s.id: s for s in steps.steps_data(ROOT / "README.md", ROOT / "docs", tmp_path).steps}
    numbers = {i: dict(s.report.numbers) for i, s in found.items() if s.report}
    _, electrical = _report("electrical")
    checks = numbers["electrical"]["Checks passing"].split(" of ")[0]
    assert f"All {checks} checks pass" in electrical
    sizing, text = _report("sizing")
    case = next(s for s in sizing["setups"] if s["name"] == sizing["sizing_case"])
    hover = numbers["sizing"][f"{case['name']}'s hover"].split(",")[0].removesuffix(" min")
    assert f"| {case['name']} |" in text and f"{hover} / " in text
    flights, text = _report("flight-sim")
    flown = len(flights["results"])
    missed = sum(1 for r in flights["results"] if r["flown"] and not r["passed"])
    assert f"{flown} of {flown} runs flown, and {missed} miss" in text
    assert numbers["flight-sim"]["PX4"] == f"{flown - missed} of {flown} runs pass"
    _, cad = _report("cad")
    weights = numbers["cad"]["Weight in the CAD"]
    assert all(f"| {w.split(' g')[0]} g |" in cad or f" {w.split(' g')[0]} g " in cad
               for w in weights.split(" to "))  # fmt: skip
    _, structure = _report("structure")
    assert (
        numbers["structure"]["Bending stress at the arm's root, full thrust"].split(",")[0]
        in structure
    )
    package = (ROOT / "docs" / "build" / "README.md").read_text(encoding="utf-8")
    for price in numbers["build"]["Bought parts, wire and plugs"].split(" to "):
        assert price.split(" ")[0] in package
    assert numbers["build"]["Bought once"].split(" ")[0] in package
    _, smart = _report("smart")
    detection = numbers["smart"]["Object detection"]
    assert detection.split(" things")[0] + " true things" in smart
    off = numbers["smart"]["Self-tuning's inertia"].split("within ")[1].split("%")[0]
    assert f"| -{off}% |" in smart  # the worst row of the report's table
    # the firmware step's are from the flight sim report's own section of it
    firmware = found["firmware"].report
    assert firmware.url.endswith("~my-firmware-the-same-scenarios")
    assert [s.text for s in firmware.sections] == ["My firmware, the same scenarios"]
    assert any("78 of 78 runs flown" in p for p in firmware.says)
