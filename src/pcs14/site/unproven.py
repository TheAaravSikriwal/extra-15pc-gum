"""What the sims can't prove, for the project site's front page: the project's own list in
decisions.md (each with the first thing to measure once it's built) and each report's "What it
can't prove". And the learning file's topics, for the step pages to point into.
"""

import json
import re
from pathlib import Path

from pcs14 import unproven
from pcs14.site import schema
from pcs14.site.steps import GITHUB

# the reports that carry their own list, by their step's name on the site
REPORTS = (
    ("Electrical", "electrical"),
    ("Flight sim", "flight-sim"),
    ("Modules in sim", "modules"),
    ("Smart features", "smart"),
    ("Structure", "structure"),
)


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
            found.append(
                schema.UnprovenItem(what=cells[0], measure=cells[1] if len(cells) > 1 else "")
            )
        elif inside:
            break
    return found


def unproven_data(docs) -> schema.Unproven:
    docs = Path(docs)
    groups = []
    decisions = docs / "decisions.md"
    if decisions.is_file():
        groups.append(schema.UnprovenGroup(
            name="The whole drone", url=GITHUB + "docs/decisions.md",
            items=project_list(decisions.read_text(encoding="utf-8"))))  # fmt: skip
    for name, folder in REPORTS:
        path = docs / "reports" / folder / f"{folder}.json"
        if not path.is_file():
            continue
        listed = json.loads(path.read_text(encoding="utf-8")).get("unproven") or []
        groups.append(schema.UnprovenGroup(
            name=name, url=GITHUB + f"docs/reports/{folder}/README.md",
            items=[schema.UnprovenItem(what=u.what, measure=u.measure)
                   for u in unproven.read(listed)]))  # fmt: skip
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
