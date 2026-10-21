"""A page per step for the project site, from what's already written: the README's live plan
(each step's status and its outcome in a line), each report's verdict and stills, and the log
entries, matched to their steps by their names. Nothing here is written twice.
"""

import re
import shutil
from dataclasses import dataclass
from pathlib import Path

from pcs14.site import schema

GITHUB = "https://github.com/TheAaravSikriwal/extra-15pc-gum/blob/main/"

# each step's id, by a word in its name in the README's plan, the report it has, and where
# that report keeps its stills
STEPS = (
    ("planning", r"Planning", None, None),
    ("setup", r"^Setup", None, None),
    ("sizing", r"Sizing", "sizing/sizing.json", "sizing/charts"),
    ("cad", r"CAD", "cad/cad.json", "cad/views"),
    ("electrical", r"Electrical", "electrical/electrical.json", "electrical/stills"),
    ("flight-sim", r"Flight sim", "flight-sim/flight-sim.json", "flight-sim/stills"),
    ("firmware", r"firmware", None, None),
    ("modules", r"Modules in sim", "modules/modules.json", "modules/stills"),
    ("smart", r"Smart features", None, None),
    ("build", r"Build package", None, None),
    ("structure", r"Structure", None, None),
    ("aero", r"Aero", None, None),
    ("design-hunt", r"Design hunt", None, None),
    ("site", r"Project site", None, None),
)
# a log entry's step, by a word in its file name (the first that matches)
LOG_WORDS = (
    ("sizing", ("sizing", "sweep", "honesty")),
    ("cad", ("cad",)),
    ("electrical", ("electrical",)),
    ("flight-sim", ("flight-sim", "first-flight")),
    ("firmware", ("firmware",)),
    ("modules", ("modules",)),
    ("aero", ("wind-tunnel",)),
    ("site", ("project-site",)),
)
# each step's topics in docs/learning.md, by their numbers there
LEARNING = {
    "planning": (1,),
    "sizing": (2, 1),
    "cad": (6, 7),
    "electrical": (15,),
    "flight-sim": (8, 1),
    "firmware": (9, 10, 11),
    "modules": (8,),
    "smart": (10,),
    "build": (12, 13),
    "structure": (16,),
    "aero": (3, 4),
    "design-hunt": (14,),
    "site": (5, 7),
}
SIZES = ("-portrait", "-square", "-vertical", "-wide")
LINK = re.compile(r"\[([^\]]+)\]\(([^)]+)\)")


@dataclass(frozen=True)
class DetailRow:
    step: str  # the step's number
    name: str
    what: str
    status: str
    outcome: str


@dataclass(frozen=True)
class PlanRow:
    number: str
    name: str
    purpose: str
    status: str
    outcome: str
    links: list
    side_track: bool


def _url(target: str) -> str:
    return target if re.match(r"^[a-z]+://", target) else GITHUB + target.lstrip("./")


def _tables(readme: str, header: tuple[str, ...]):
    """Each row of the README's tables whose header starts with one of `header`, with that
    header."""
    current = None
    for line in readme.splitlines():
        if not line.startswith("|"):
            current = None
            continue
        if line.startswith("|---"):
            continue
        if line.startswith(header):
            current = line
            continue
        if current is not None:
            yield current, [c.strip() for c in line.strip().strip("|").split("|")]


def detail_rows(readme: str) -> list[DetailRow]:
    """The "in detail" tables' rows: each step's talk, plan, build and the rest."""
    rows = []
    for _, cells in _tables(readme, ("| Part",)):
        m = re.match(r"^(\d+)[a-z]\.", cells[0])
        if m and len(cells) >= 4:
            rows.append(DetailRow(m.group(1), cells[0], cells[1], cells[2],
                                  LINK.sub(r"\1", cells[3])))  # fmt: skip
    return rows


def plan_rows(readme: str) -> list[PlanRow]:
    """The steps and side tracks from the README's two plan tables."""
    rows = []
    for header, cells in _tables(readme, ("| Step", "| Side track")):
        side = header.startswith("| Side track")
        if len(cells) < 4:
            continue
        first, purpose, status, outcome = cells[:4]
        m = re.match(r"^(\d+)\.\s*(.*)$", first)
        number, name = (m.group(1), m.group(2)) if m else ("", first)
        links = [schema.Link(text=t, url=_url(u)) for t, u in LINK.findall(outcome)]
        rows.append(PlanRow(number, name, purpose, status, LINK.sub(r"\1", outcome), links, side))
    return rows


def step_of(log_name: str) -> str:
    for step, words in LOG_WORDS:
        if any(w in log_name for w in words):
            return step
    return "planning"


def _stills(source: Path, step: str, out: Path) -> list[str]:
    """One size of each still (the wide one where there are several), copied under `out`."""
    if not source.is_dir():
        return []
    files = sorted(source.glob("*.png"))
    groups: dict[str, list[Path]] = {}
    for f in files:
        base = f.stem
        for size in SIZES:
            base = base.removesuffix(size)
        groups.setdefault(base, []).append(f)
    picked = []
    for base, found in groups.items():
        wide = [f for f in found if f.stem.endswith("-wide")]
        f = wide[0] if wide else next((f for f in found if f.stem == base), found[0])
        target = out / "stills" / step / f.name
        target.parent.mkdir(parents=True, exist_ok=True)
        shutil.copyfile(f, target)
        picked.append(f"stills/{step}/{f.name}")
    return picked


def _logs(log_folder: Path) -> dict[str, list[schema.LogEntry]]:
    found: dict[str, list[schema.LogEntry]] = {}
    for f in sorted(log_folder.glob("*.md")):
        heading = next((line[2:].strip() for line in f.read_text(encoding="utf-8").splitlines()
                        if line.startswith("# ")), f.stem)  # fmt: skip
        entry = schema.LogEntry(title=heading, date=f.name[:10],
                                url=GITHUB + f"docs/log/{f.name}")  # fmt: skip
        found.setdefault(step_of(f.name), []).append(entry)
    return found


def steps_data(readme_path, docs, out) -> schema.Steps:
    import json

    docs, out = Path(docs), Path(out)
    from pcs14.site.unproven import learning_topics

    logs = _logs(docs / "log")
    learning = docs / "learning.md"
    topics = learning_topics(learning.read_text(encoding="utf-8")) if learning.is_file() else {}
    readme = Path(readme_path).read_text(encoding="utf-8")
    details = detail_rows(readme)
    made = []
    for row in plan_rows(readme):
        found = next(((i, r, s) for i, pattern, r, s in STEPS if re.search(pattern, row.name)),
                     (row.name.lower().replace(" ", "-"), None, None))  # fmt: skip
        step_id, report_file, stills = found
        report = None
        if report_file and (docs / "reports" / report_file).is_file():
            data = json.loads((docs / "reports" / report_file).read_text(encoding="utf-8"))
            report = schema.ReportRef(
                verdict=data.get("verdict"), generated=data.get("generated"),
                url=GITHUB + f"docs/reports/{Path(report_file).parent.as_posix()}/README.md",
            )  # fmt: skip
        made.append(schema.Step(
            id=step_id, number=row.number, name=row.name, purpose=row.purpose,
            status=row.status, outcome=row.outcome, links=row.links, side_track=row.side_track,
            report=report,
            stills=_stills(docs / "reports" / stills, step_id, out) if stills else [],
            logs=logs.get(step_id, []),
            parts=[schema.StepPart(name=d.name, what=d.what, status=d.status, outcome=d.outcome)
                   for d in details if row.number and d.step == row.number],
            learning=[topics[n] for n in LEARNING.get(step_id, ()) if n in topics],
        ))  # fmt: skip
    return schema.Steps(schema_version=schema.SCHEMA_VERSION, steps=made)
