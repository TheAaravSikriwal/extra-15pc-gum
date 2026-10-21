"""The project site's unproven list: what the sims can't prove, from decisions.md's own list
and each report's, and the step pages' links into the learning file."""

from pathlib import Path

from pcs14.site import schema, steps
from pcs14.site.unproven import learning_topics, project_list, unproven_data

ROOT = Path(__file__).resolve().parents[1]

DECISIONS = """### A research project

**The unproven list.** Simulation can't prove everything:

| What sim can't prove | First thing to measure when built |
|---|---|
| Real thrust (data runs +-15%) | One motor and prop on a thrust stand |
| Vibration reaching the IMU | A gyro log with the props spinning |

**Two optional purchases:** a thrust stand.
"""


def test_the_projects_list_is_decisions_own_table():
    found = project_list(DECISIONS)
    assert [i.what for i in found] == [
        "Real thrust (data runs +-15%)",
        "Vibration reaching the IMU",
    ]
    assert found[1].measure == "A gyro log with the props spinning"
    assert project_list("nothing here") == []


def test_the_real_list_has_the_projects_and_each_reports(tmp_path):
    found = unproven_data(ROOT / "docs")
    names = [g.name for g in found.groups]
    assert names[0] == "The whole drone" and "Electrical" in names and "Flight sim" in names
    electrical = next(g for g in found.groups if g.name == "Electrical")
    assert any("battery leads" in i.what for i in electrical.items)
    assert electrical.url.endswith("docs/reports/electrical/README.md")
    assert found.schema_version == schema.SCHEMA_VERSION


def test_a_steps_learning_links_point_at_the_learning_files_headings(tmp_path):
    topics = learning_topics((ROOT / "docs" / "learning.md").read_text(encoding="utf-8"))
    assert topics[9].text == "Control systems and PID"
    assert topics[4].url.endswith("docs/learning.md#4-cfd-the-virtual-wind-tunnel")
    found = steps.steps_data(ROOT / "README.md", ROOT / "docs", tmp_path)
    by_id = {s.id: s for s in found.steps}
    assert [link.text for link in by_id["firmware"].learning][:2] == [
        "Control systems and PID", "Sensor fusion and state estimation"]  # fmt: skip
    assert by_id["setup"].learning == []
