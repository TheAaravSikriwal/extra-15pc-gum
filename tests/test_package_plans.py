"""The build package's test plans and legal checklist."""

from pcs14.package import legal, testplans
from pcs14.unproven import Unproven

SAFETY_RULES = (  # CLAUDE.md's safety rules, each needing a test before the first flight
    "kill switch override everything",
    "two separate boards",
    "loses power, the drone keeps flying",
    "never the main power",
    "shadow mode",
    "cut before the parachute",
    "hung CPU",
    "never depends on the companion",
    "never commands the motors",
)


def test_every_safety_rule_has_a_bench_check():
    rules = " | ".join(testplans.safety_rules())
    for rule in SAFETY_RULES:
        assert rule in rules, rule


def test_every_unproven_measurement_is_in_the_plan():
    groups = [("A report", [Unproven(what="The jolt.", measure="A load cell on the riser."),
                            Unproven(what="Old item.", measure="")])]  # fmt: skip
    electrical = {"cases": [{"setup": "base", "case": "hover", "battery_amps": 14.6},
                            {"setup": "base", "case": "burst", "battery_amps": 90.0}]}  # fmt: skip
    text = testplans.render(electrical, groups, "2026-10-21")
    assert "| The jolt. | A load cell on the riser. |" in text
    assert "| base | 14.6 A |" in text and "90.0 A" not in text


def test_every_legal_rule_names_its_source_and_where_it_lives():
    for rule in legal.RULES:
        assert rule.source.startswith(("https://www.faa.gov/", "https://www.ecfr.gov/"))
        assert rule.setting
    text = legal.render("2026-10-21")
    assert "not opened on the day" in text and "121.92 m" in text
