"""A page per step for the project site, from what's already written: the README's live plan
(each step's status, and its outcome in a line as I wrote it when the step finished), each
report as it stands now (its verdict in its own words, its key numbers and its sections), its
stills, and the log entries, matched to their steps by their names. Nothing here is written
twice.
"""

import json
import posixpath
import re
import shutil
from collections import Counter
from dataclasses import dataclass
from pathlib import Path
from typing import NamedTuple

from pcs14.site import schema

GITHUB = "https://github.com/TheAaravSikriwal/extra-15pc-gum/blob/main/"


class Source(NamedTuple):
    id: str
    pattern: str  # a word in its name in the README's plan
    report: str | None  # its report's data, under docs/reports
    stills: str | None  # where that report keeps its stills
    verdict: str | None  # the report's heading its verdict is under; None for its opening


STEPS = (
    Source("planning", r"Planning", None, None, None),
    Source("setup", r"^Setup", None, None, None),
    Source("sizing", r"Sizing", "sizing/sizing.json", "sizing/charts", "The verdict"),
    Source("cad", r"CAD", "cad/cad.json", "cad/views", "The verdict"),
    Source(
        "electrical",
        r"Electrical",
        "electrical/electrical.json",
        "electrical/stills",
        "The verdict",
    ),  # fmt: skip
    Source(
        "flight-sim",
        r"Flight sim",
        "flight-sim/flight-sim.json",
        "flight-sim/stills",
        "The verdict",
    ),  # fmt: skip
    # my firmware flies the flight sim's scenarios, so its numbers are in that report
    Source(
        "firmware",
        r"firmware",
        "flight-sim/flight-sim.json",
        None,
        "My firmware, the same scenarios",
    ),  # fmt: skip
    Source("modules", r"Modules in sim", "modules/modules.json", "modules/stills", "The verdict"),
    Source("smart", r"Smart features", "smart/smart.json", "smart/stills", "The verdict"),
    Source("build", r"Build package", "../build/package.json", None, None),
    Source(
        "structure", r"Structure", "structure/structure.json", "structure/stills", "The verdict"
    ),  # fmt: skip
    Source("aero", r"Aero", None, None, None),
    Source("design-hunt", r"Design hunt", None, None, None),
    Source("site", r"Project site", None, None, None),
)
# a log entry's step, by a word in its file name (the first that matches)
LOG_WORDS = (
    ("planning", ("planning", "plan-review", "plan-revision", "research-project", "soar-mode")),
    ("setup", ("moving-to-the-pc",)),
    ("sizing", ("sizing", "sweep")),
    ("cad", ("cad",)),
    ("electrical", ("electrical",)),
    ("flight-sim", ("flight-sim", "first-flight")),
    ("firmware", ("firmware",)),
    ("modules", ("modules",)),
    ("smart", ("smart-features",)),
    ("structure", ("structure",)),
    ("build", ("build-package",)),
    ("aero", ("wind-tunnel",)),
    ("site", ("project-site", "drone-view", "the-docs")),
)
# each step's topics in docs/learning.md, by their numbers there
LEARNING = {
    "planning": (1,),
    "sizing": (2, 1),
    "cad": (6, 7),
    "electrical": (15,),
    "flight-sim": (8, 1),
    "firmware": (9, 10, 11),
    "modules": (8, 17),
    "smart": (10, 18),
    "build": (12, 13),
    "structure": (16,),
    "aero": (3, 4, 19),
    "design-hunt": (14,),
    "site": (5, 7),
}
SIZES = ("-portrait", "-square", "-vertical", "-wide")
LINK = re.compile(r"\[([^\]]+)\]\(([^)]+)\)")
# a parenthesis of nothing but links, "([report](...), [log](...))": the page lists them below
LINKS_ONLY = re.compile(r"\s*\(\s*\[[^\]]+\]\([^)]*\)(?:\s*,\s*\[[^\]]+\]\([^)]*\))*\s*\)")


@dataclass(frozen=True)
class DetailRow:
    step: str  # the step's number
    name: str
    what: str
    status: str
    outcome: str
    links: list


@dataclass(frozen=True)
class PlanRow:
    number: str
    name: str
    purpose: str
    status: str
    outcome: str
    links: list
    side_track: bool
    starts_after: str = ""


def _url(target: str, docs: frozenset[str] = frozenset()) -> str:
    """Where a README link goes on the site: into the library when it's a doc there (an
    anchor after a ~), GitHub for anything else."""
    if re.match(r"^[a-z]+://", target):
        return target
    target = target.lstrip("./")
    path, _, frag = target.partition("#")
    if path in docs:
        return f"#/library/{path.removesuffix('.md')}" + (f"~{frag}" if frag else "")
    return GITHUB + target


def _links(cell: str, docs: frozenset[str]) -> list[schema.Link]:
    """A cell's links, each label once: a label used twice gets its file's date."""
    found = LINK.findall(cell)
    used = Counter(text for text, _ in found)
    links = []
    for text, url in found:
        if used[text] > 1:
            date = re.search(r"\d{4}-\d{2}-\d{2}", url)
            text = f"{text}, {date.group(0) if date else Path(url.partition('#')[0]).stem}"
        links.append(schema.Link(text=text, url=_url(url, docs)))
    return links


def _plain(text: str) -> str:
    """Markdown to plain words: the link-only parentheses out, other links to their words."""
    text = LINK.sub(r"\1", LINKS_ONLY.sub("", text))
    return re.sub(r"\*\*|`", "", text).strip()


def _tables(readme: str, header: tuple[str, ...]):
    """Each row of the README's tables whose header starts with one of `header`, with that
    header's column names."""
    current = None
    for line in readme.splitlines():
        if not line.startswith("|"):
            current = None
            continue
        if line.startswith("|---"):
            continue
        if line.startswith(header):
            current = [c.strip() for c in line.strip().strip("|").split("|")]
            continue
        if current is not None:
            yield current, [c.strip() for c in line.strip().strip("|").split("|")]


def detail_rows(readme: str, docs: frozenset[str] = frozenset()) -> list[DetailRow]:
    """The "in detail" tables' rows: each step's talk, plan, build and the rest."""
    rows = []
    for _, cells in _tables(readme, ("| Part",)):
        m = re.match(r"^(\d+)[a-z]\.", cells[0])
        if m and len(cells) >= 4:
            rows.append(DetailRow(m.group(1), cells[0], _plain(cells[1]), cells[2],
                                  _plain(cells[3]), _links(cells[3], docs)))  # fmt: skip
    return rows


def plan_rows(readme: str, docs: frozenset[str] = frozenset()) -> list[PlanRow]:
    """The steps and side tracks from the README's two plan tables, read by their columns'
    names."""
    rows = []
    for names, cells in _tables(readme, ("| Step", "| Side track")):
        if len(cells) < 3:
            continue
        cell = dict(zip(names, cells, strict=False))
        m = re.match(r"^(\d+)\.\s*(.*)$", cells[0])
        number, name = (m.group(1), m.group(2)) if m else ("", cells[0])
        outcome = cell.get("Outcome", "")
        rows.append(PlanRow(number, name, cell.get("What it's for", ""), cell.get("Status", ""),
                            _plain(outcome), _links(outcome, docs), names[0] == "Side track",
                            cell.get("Starts after", "")))  # fmt: skip
    return rows


def step_of(log_name: str) -> str | None:
    for step, words in LOG_WORDS:
        if any(w in log_name for w in words):
            return step
    return None


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


def _logs(log_folder: Path) -> dict[str | None, list[schema.LogEntry]]:
    found: dict[str | None, list[schema.LogEntry]] = {}
    for f in sorted(log_folder.glob("*.md")):
        heading = next((line[2:].strip() for line in f.read_text(encoding="utf-8").splitlines()
                        if line.startswith("# ")), f.stem)  # fmt: skip
        date = f.name[:10]
        entry = schema.LogEntry(title=heading.removeprefix(f"{date}: "), date=date,
                                url=f"#/library/docs/log/{f.stem}")  # fmt: skip
        found.setdefault(step_of(f.name), []).append(entry)
    return found


def _folder(report_file: str) -> str:
    """The report's folder in the repo, "../build" and all resolved."""
    return posixpath.normpath(f"docs/reports/{Path(report_file).parent.as_posix()}")


# --- the reports as they stand now ---------------------------------------------------------


def says(report: str, heading: str | None) -> list[str]:
    """A report's verdict in its own words: the paragraphs under `heading`, or before the
    first heading, without its pictures, tables or lists."""
    paragraphs, current, inside = [], [], heading is None
    for line in report.splitlines() + [""]:
        if line.startswith("## "):
            if inside and heading is None:
                break
            inside = line[3:].strip() == heading
            continue
        if not inside or line.startswith(("# ", "|", "!", "- ", "*Generated")):
            line = ""
        if line.strip():
            current.append(line.strip())
        elif current:
            said = _plain(" ".join(current))
            if not said.endswith(":"):  # not the line that leads into a list or table
                paragraphs.append(said[:1].upper() + said[1:])
            current = []
    return paragraphs


def sections(report: str, route: str, heading: str | None) -> list[schema.Link]:
    """The report's sections, each a link to it in the library: `heading` alone, if it's a
    section of a bigger report."""
    from pcs14.site.markdown import anchor

    found = [line[3:].strip() for line in report.splitlines() if line.startswith("## ")]
    if heading not in (None, "The verdict"):
        found = [h for h in found if h == heading]
    return [schema.Link(text=h, url=f"#/library/{route}~{anchor(h)}") for h in found]


def _of(found: list, key: str = "passed") -> str:
    return f"{sum(1 for x in found if x[key])} of {len(found)}"


def _runs(results: list) -> str:
    flown = sum(1 for r in results if r["flown"])
    words = f"{_of(results)} runs pass"
    return words if flown == len(results) else f"{words}, {flown} flown"


def _sizing(d: dict) -> list[list[str]]:
    from pcs14.site.data import _shown

    setups = d["setups"]
    every = all(s["verdict"] == "pass" for s in setups if s.get("required"))
    passing = sum(1 for s in setups if s["verdict"] == "pass")
    rows = [["Setups passing", f"{passing} of {len(setups)}" + (", every required one" if every
                                                                else "")]]  # fmt: skip
    for s in setups:
        for c in s["checks"]:
            if c["verdict"] != "pass":
                shown = _shown(c)
                optional = "" if s.get("required") else ", an optional setup,"
                rows.append([f"{s['name']}{optional} misses", f"its {c['name'].lower()}: "
                             f"{shown['shown']}, {shown['shown_limit']}"])  # fmt: skip
    case = next(s for s in setups if s["name"] == d["sizing_case"])
    rows.append(["The sizing case", f"{case['name']}, {case['mass_g']:.0f} g with "
                 f"{case['growth_margin_g']:.0f} g of growth margin"])  # fmt: skip
    for c in case["checks"]:
        if c["name"] == "Hover time":
            shown = _shown(c)
            hover = f"{shown['shown']}, {shown['shown_pessimistic']} pessimistic"
            rows.append([f"{case['name']}'s hover", f"{hover} ({shown['shown_limit']})"])
    return rows


def _cad(d: dict) -> list[list[str]]:
    combos = d["combinations"]
    light = min(combos, key=lambda c: c["mass_g"])
    heavy = max(combos, key=lambda c: c["mass_g"])
    return [
        ["Combinations passing every check", _of(combos)],
        ["Pieces", f"{len(d['pieces'])}, and {len(d['printed_parts'])} printed parts of my own"],
        [
            "Weight in the CAD",
            f"{light['mass_g']:.0f} g ({light['setup']}) to "
            f"{heavy['mass_g']:.0f} g ({heavy['setup']})",
        ],
        [
            "Parts with a dimension I estimated",
            f"{len(d['estimates'])}, where the maker doesn't publish it",
        ],
    ]


def _electrical(d: dict) -> list[list[str]]:
    listed = d["connection_list"]
    sims = d["switch_sims"]
    behaved = sum(1 for s in sims if s["passed"] == s["meant_to_pass"])
    problems = len(d["rule_problems"])
    return [
        ["Checks passing", f"{_of(d['findings'])}, in all {len(d['combinations'])} combinations"],
        [
            "The connection list",
            f"{listed['boards']} boards, {listed['wires']} wires and "
            f"{listed['safety_paths']} safety paths",
        ],
        ["Wiring rule problems", str(problems) if problems else "none"],
        ["The safety switch in ngspice", f"{behaved} of {len(sims)} cases do what they should"],
        ["KiCad's rule check", f"{d['kicad_rules_violations'] or 'no'} violations"],
    ]


def _flight_sim(d: dict) -> list[list[str]]:
    times = d["closing"]["flight_time"]
    hover = max(abs(round(t["hover_sim_min"], 1) - round(t["hover_sizing_min"], 1))
                for t in times)  # fmt: skip
    under = [1 - t["cruise_sim_min"] / t["cruise_sizing_min"] for t in times]
    misses = Counter(r["scenario"] for r in d["results"] if r["flown"] and not r["passed"])
    return [
        ["PX4", _runs(d["results"])],
        ["The misses, by scenario", ", ".join(f"{s} in {n}" for s, n in misses.items()) or "none"],
        [
            "Hover time, the sim against the sizing model",
            f"within {hover:.1f} min, in every combination",
        ],
        [
            "Cruise time, the same",
            f"{min(under) * 100:.0f} to {max(under) * 100:.0f}% under the sizing model",
        ],
    ]


def _firmware(d: dict) -> list[list[str]]:
    mine = d["mine"]["results"]
    px4 = {(r["scenario"], r["setup"]): r["passed"] for r in d["results"]}
    only_mine = [r for r in mine if r["passed"] and not px4.get((r["scenario"], r["setup"]), True)]
    only_px4 = [r for r in mine if not r["passed"] and px4.get((r["scenario"], r["setup"]))]
    word = lambda found: ", ".join(f"{r['scenario']} in {r['setup']}" for r in found) or "none"  # noqa: E731
    return [
        ["My firmware", _runs(mine)],
        ["PX4, the same runs", _runs(d["results"])],
        ["Where mine passes and PX4 misses", word(only_mine)],
        ["Where PX4 passes and mine misses", word(only_px4)],
    ]


def _modules(d: dict) -> list[list[str]]:
    fired = len(d["false_triggers"])
    return [
        ["Runs passing", _of(d["runs"])],
        [
            "The safety monitor's triggers on healthy runs",
            f"{fired or 'none'} fired, over "
            f"{d['healthy_runs']} runs where nothing fails on purpose",
        ],
    ]


def _smart(d: dict) -> list[list[str]]:
    t = d["detection"]["totals"]
    tuning = d["tuning"]
    # rounded as the report's table rounds it
    off = max(abs(x["found_kg_m2"] - x["model_kg_m2"]) / x["model_kg_m2"] for x in tuning)
    return [
        ["Runs passing", _of(d["runs"])],
        [
            "Self-tuning's inertia",
            f"within {off * 100:.1f}% of the model, in all {len(tuning)} combinations",
        ],
        [
            "Object detection",
            f"{t['near']} of {t['true']} things boxed (median overlap {t['median overlap']:.2f}), "
            f"{t['false alarms']} false alarms over {t['frames']} frames, by "
            f"{d['detection']['model']}",
        ],
    ]


def _build(d: dict) -> list[list[str]]:
    totals = [t for t in d["totals"] if t["setup"] != "once"]
    once = next((t for t in d["totals"] if t["setup"] == "once"), None)
    cheap = min(totals, key=lambda t: t["usd"])
    dear = max(totals, key=lambda t: t["usd"])
    rows = [["Bought parts, wire and plugs", f"${cheap['usd']:,.2f} ({cheap['setup']}) to "
             f"${dear['usd']:,.2f} ({dear['setup']})"]]  # fmt: skip
    if once:
        rows.append(
            ["Bought once", f"${once['usd']:,.2f} priced so far, {once['unpriced']} not yet"]
        )
    rows += [
        ["Not priced yet", f"up to {max(t['unpriced'] for t in totals)} lines in a combination"],
        ["Lines on the parts list", str(len(d["lines"]))],
        ["Open problems", f"{len(d['open'])}, in the package's own list"],
    ]
    return rows


def _structure(d: dict) -> list[list[str]]:
    from pcs14.structure.report import STRENGTH_MPA

    stress = d["root_stress_mpa"]
    rows = [["Bending stress at the arm's root, full thrust", f"{stress:.0f} MPa, against at least "
             f"{STRENGTH_MPA:g} MPa: {STRENGTH_MPA / stress:.1f} times"]]  # fmt: skip
    modes = [f"{m['name']}, {m['low_hz']:.0f} to {m['high_hz']:.0f} Hz" for m in d["modes"]]
    rows.append(["The arm's first two bending modes", "; ".join(modes)])
    near: dict[tuple[str, int], list[str]] = {}
    for n in d["near"]:
        near.setdefault((n["mode"], n["per_turn"]), []).append(n["setup"])
    for (mode, per), setups in near.items():
        what = "once a turn" if per == 1 else f"{per} a turn"
        rows.append([f"Shaken near its mode in a hover: {mode}", f"{what}, in {', '.join(setups)}"])
    weakest = min(d["joints"], key=lambda j: j["margin_low"])
    margin = f"{weakest['margin_low']:.1f} to {weakest['margin_high']:.1f}"
    rows.append(["The chute mount's weakest joint",
                 f"{weakest['name']}: {margin} times the opening jolt's bound"])  # fmt: skip
    return rows


NUMBERS = {
    "sizing": _sizing,
    "cad": _cad,
    "electrical": _electrical,
    "flight-sim": _flight_sim,
    "firmware": _firmware,
    "modules": _modules,
    "smart": _smart,
    "build": _build,
    "structure": _structure,
}


def report_now(source: Source, docs: Path) -> schema.ReportRef | None:
    """A step's report as it stands now: its verdict, its own words for it, its key numbers
    and its sections, each a link into the library."""
    path = docs / "reports" / source.report if source.report else None
    if path is None or not path.is_file():
        return None
    data = json.loads(path.read_text(encoding="utf-8"))
    folder = _folder(source.report)
    readme = docs.parent / folder / "README.md"
    text = readme.read_text(encoding="utf-8") if readme.is_file() else ""
    route = f"{folder}/README"
    anchor = ""
    if source.verdict not in (None, "The verdict"):
        from pcs14.site.markdown import anchor as anchor_of

        anchor = f"~{anchor_of(source.verdict)}"
    return schema.ReportRef(
        verdict=data.get("verdict") if source.verdict in (None, "The verdict")
        else data.get("mine", {}).get("verdict"),
        generated=data.get("generated"), url=f"#/library/{route}{anchor}",
        says=says(text, source.verdict), numbers=NUMBERS[source.id](data) if source.id in NUMBERS
        else [], sections=sections(text, route, source.verdict),
    )  # fmt: skip


def steps_data(readme_path, docs, out) -> schema.Steps:
    docs, out = Path(docs), Path(out)
    from pcs14.site.library import _docs
    from pcs14.site.unproven import learning_topics

    library = frozenset(rel for _, rel in _docs(Path(readme_path).parent))
    logs = _logs(docs / "log")
    learning = docs / "learning.md"
    topics = learning_topics(learning.read_text(encoding="utf-8")) if learning.is_file() else {}
    readme = Path(readme_path).read_text(encoding="utf-8")
    details = detail_rows(readme, library)
    made = []
    for row in plan_rows(readme, library):
        source = next((s for s in STEPS if re.search(s.pattern, row.name)),
                      Source(row.name.lower().replace(" ", "-"), "", None, None, None))  # fmt: skip
        made.append(schema.Step(
            id=source.id, number=row.number, name=row.name, purpose=row.purpose,
            status=row.status, outcome=row.outcome, links=row.links, side_track=row.side_track,
            starts_after=row.starts_after, report=report_now(source, docs),
            stills=_stills(docs / "reports" / source.stills, source.id, out) if source.stills
            else [],
            logs=logs.get(source.id, []),
            parts=[schema.StepPart(name=d.name, what=d.what, status=d.status, outcome=d.outcome,
                                   links=d.links)
                   for d in details if row.number and d.step == row.number],
            learning=[topics[n] for n in LEARNING.get(source.id, ()) if n in topics],
        ))  # fmt: skip
    return schema.Steps(schema_version=schema.SCHEMA_VERSION, steps=made)
