"""What the sims can't prove, for the project site: the project's own list in decisions.md (each
with the first thing to measure once it's built), each report's "What it can't prove" under its
step's name, and what STATUS.md still has open. And the learning file's topics, for the step
pages to point into.
"""

import json
import re
from pathlib import Path

from pcs14 import unproven
from pcs14.site import schema
from pcs14.site.steps import GITHUB

# the reports that carry their own list, by their step's name and id on the site
REPORTS = (
    ("3. Electrical design", "electrical", "electrical"),
    ("4. Flight sim (PX4)", "flight-sim", "flight-sim"),
    ("6. Modules in sim", "modules", "modules"),
    ("7. Smart features in sim", "smart", "smart"),
    ("Structure (side track)", "structure", "structure"),
)
# what decisions.md's rows point at that's further down decisions.md, worded for the site
ON_THE_SITE = {"(see the honesty check below)": "(see the honesty check in the decisions)"}


def project_list(decisions: str) -> list[schema.UnprovenItem]:
    """decisions.md's "The unproven list" table."""
    found, inside = [], False
    for line in decisions.splitlines():
        if line.startswith("| What sim can't prove"):
            inside = True
            continue
        if inside and line.startswith("|---"):
            continue
        if inside and line.startswith("|"):
            cells = [c.strip() for c in line.strip().strip("|").split("|")]
            what = cells[0]
            for said, site in ON_THE_SITE.items():
                what = what.replace(said, site)
            found.append(schema.UnprovenItem(what=what, measure=cells[1] if len(cells) > 1 else ""))
        elif inside:
            break
    return found


def still_open(status: str) -> list[schema.UnprovenItem]:
    """STATUS.md's "Still open" list, each item a line."""
    found, inside = [], False
    for line in status.splitlines():
        if line.startswith("## "):
            inside = line.strip() == "## Still open"
            continue
        if inside and line.startswith("- "):
            found.append(schema.UnprovenItem(what=line[2:].strip()))
    return found


def unproven_data(docs) -> schema.Unproven:
    docs = Path(docs)
    groups = []
    decisions = docs / "decisions.md"
    if decisions.is_file():
        groups.append(schema.UnprovenGroup(
            name="The whole drone", url="#/library/docs/decisions",
            items=project_list(decisions.read_text(encoding="utf-8"))))  # fmt: skip
    for name, folder, step in REPORTS:
        path = docs / "reports" / folder / f"{folder}.json"
        if not path.is_file():
            continue
        listed = json.loads(path.read_text(encoding="utf-8")).get("unproven") or []
        groups.append(schema.UnprovenGroup(
            name=name, url=f"#/library/docs/reports/{folder}/README", step=step,
            items=[schema.UnprovenItem(what=u.what, measure=u.measure)
                   for u in unproven.read(listed)]))  # fmt: skip
    status = docs.parent / "STATUS.md"
    if status.is_file():
        opened = still_open(status.read_text(encoding="utf-8"))
        if opened:
            groups.append(schema.UnprovenGroup(name="Still open", url="#/library/STATUS",
                                               items=opened))  # fmt: skip
    return schema.Unproven(schema_version=schema.SCHEMA_VERSION, groups=groups)


def _anchor(heading: str) -> str:
    """GitHub's anchor for a heading: lower case, punctuation out, spaces to hyphens."""
    return re.sub(r"[^a-z0-9 -]", "", heading.lower()).replace(" ", "-")


def learning_topics(learning: str) -> dict[int, schema.Link]:
    """The learning file's numbered topics ("## 9. Control systems and PID"), by number."""
    found = {}
    for line in learning.splitlines():
        m = re.match(r"^## (\d+)\. (.+)$", line)
        if m:
            found[int(m.group(1))] = schema.Link(
                text=m.group(2).strip(),
                url=GITHUB + "docs/learning.md#" + _anchor(line[3:].strip()),
            )
    return found
