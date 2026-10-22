"""Everything else, for the site: every Markdown doc in the repo rendered (the library), every
catalog part with every field (for the parts page), every report's own data file and every file
the site itself reads (the data), and how each number is worked out, from the code's own
explanations (the math).

Links between docs stay on the site (#/library/docs/log/x, an anchor after a ~), pictures and
small files the docs point at are copied beside the data, and anything else points at GitHub.
"""

import ast
import json
import posixpath
import re
import shutil
import subprocess
from pathlib import Path

from pcs14.site import markdown, schema
from pcs14.site.steps import GITHUB, LINK, step_of, step_titles

# the library's fixed sections, in order: (name, the repo paths or globs that go in it). The
# work by topic (each step's specs, plans and log posts) goes between the build package and
# the repo's folders.
SECTIONS = (
    (
        "The project",
        (
            "README.md",
            "STATUS.md",
            "docs/decisions.md",
            "docs/roadmap.md",
            "docs/learning.md",
            "docs/style.md",
        ),
    ),
    (
        "Reports",
        (
            "docs/reports/sizing/README.md",
            "docs/reports/sizing/validation.md",
            "docs/reports/cad/README.md",
            "docs/reports/electrical/README.md",
            "docs/reports/flight-sim/README.md",
            "docs/reports/modules/README.md",
            "docs/reports/smart/README.md",
            "docs/reports/structure/README.md",
        ),
    ),
    (
        "The build package",
        (
            "docs/build/README.md",
            "docs/build/parts.md",
            "docs/build/assembly.md",
            "docs/build/wiring.md",
            "docs/build/firmware.md",
            "docs/build/tests.md",
            "docs/build/legal.md",
        ),
    ),
    (
        "The repo's folders",
        (
            "design/README.md",
            "design/catalog/README.md",
            "design/validation/README.md",
            "sizing/README.md",
            "cad/README.md",
            "sim/README.md",
            "aero/README.md",
            "explore/README.md",
            "media/README.md",
        ),
    ),
    (
        "Behind the scenes",
        (
            "CLAUDE.md",
            "docs/setup-pc.md",
            "docs/machines/README.md",
            "docs/machines/*.md",
            "scripts/README.md",
        ),
    ),
)
TOPICS = (("spec", "docs/specs/*.md"), ("plan", "docs/plans/*.md"), ("log", "docs/log/*.md"))
TOPICS_GROUP = "The work, by topic"
ABOUT = {
    TOPICS_GROUP: "Each step's specs, plans and log posts together, the newest topic first.",
    "Behind the scenes": "Notes for my two machines and for the AI I pair with: how each machine "
    "is set up, what its check found, and the rules a session follows.",
}
# a folder's README is titled by its path; on the site it gets what it holds, too
FOLDERS = {
    "design/": "the drone on paper",
    "design/catalog/": "the real parts",
    "design/validation/": "the honesty check's builds",
    "sizing/": "the sizing model",
    "cad/": "the drone as code",
    "sim/": "the flight sim's own part",
    "aero/": "the virtual wind tunnel",
    "explore/": "the design hunt",
    "media/": "pictures for posts",
    "scripts/": "setup and helpers",
    "docs/machines/": "each machine's check",
}
COPIED = (".png", ".jpg", ".jpeg", ".gif", ".svg", ".csv", ".txt")  # files the docs point at
SUPERSEDED = re.compile(r"^\*((?:Partly superseded|Superseded)\b.*?)\*$", re.M)


def _docs(root: Path) -> list[tuple[str, str]]:
    """(section, repo path) for every doc, each once: the fixed sections' in their order, and
    the topics' under TOPICS_GROUP."""
    seen, out = set(), []
    patterns = [(s, p) for s, ps in SECTIONS for p in ps] + [(TOPICS_GROUP, p) for _, p in TOPICS]
    for section, pattern in patterns:
        found = sorted(root.glob(pattern)) if "*" in pattern else [root / pattern]
        for path in found:
            rel = path.relative_to(root).as_posix()
            if path.is_file() and rel not in seen:
                seen.add(rel)
                out.append((section, rel))
    return out


def _title(text: str, rel: str) -> str:
    m = re.search(r"^# (.+)$", text, re.M)
    title = m.group(1).strip() if m else Path(rel).stem.replace("-", " ")
    if title in FOLDERS:
        title = f"{title}: {FOLDERS[title]}"
    # a dated doc's date is shown beside it
    return re.sub(r"^\d{4}-\d{2}-\d{2}: ", "", title)


def superseded(text: str) -> str | None:
    """The doc's own line saying it's superseded, in plain words, if it has one near the top."""
    head = "\n".join(text.splitlines()[:8])
    m = SUPERSEDED.search(head)
    return LINK.sub(r"\1", m.group(1)).strip() if m else None


def route_of(rel: str) -> str:
    """A doc's place on the site: its repo path without .md."""
    return rel[:-3] if rel.endswith(".md") else rel


def _rewriters(rel: str, docs: set[str], root: Path, out: Path, copied: set[str]):
    here = posixpath.dirname(rel)

    def resolve(url: str) -> tuple[str, str]:
        path, _, frag = url.partition("#")
        return posixpath.normpath(posixpath.join(here, path)) if path else rel, frag

    def link(url: str) -> str:
        if re.match(r"^[a-z]+:", url):
            return url
        if url.startswith("#"):
            return f"#/library/{route_of(rel)}~{url[1:]}"
        target, frag = resolve(url)
        if target in docs:
            return f"#/library/{route_of(target)}" + (f"~{frag}" if frag else "")
        if target.lower().endswith(COPIED) and (root / target).is_file():
            copied.add(target)
            return f"./data/library/files/{target}"
        return GITHUB + target + (f"#{frag}" if frag else "")

    def image(url: str) -> str:
        if re.match(r"^[a-z]+:", url):
            return url
        target, _ = resolve(url)
        if (root / target).is_file():
            copied.add(target)
            return f"./data/library/files/{target}"
        return GITHUB + target

    return link, image


def _added(root: Path) -> dict[str, int]:
    """When git first saw each dated doc, to order a day's docs newest first. Empty outside a
    repo, where the names order them."""
    try:
        said = subprocess.run(
            ["git", "log", "--diff-filter=A", "--name-only", "--format=@%ct", "--",
             "docs/specs", "docs/plans", "docs/log"],
            cwd=root, capture_output=True, text=True, check=True,
        ).stdout  # fmt: skip
    except (OSError, subprocess.CalledProcessError):
        return {}
    found, when = {}, 0
    for line in said.splitlines():
        if line.startswith("@"):
            when = int(line[1:])
        elif line.strip():
            found[line.strip()] = when  # newest first, so the last one seen is its first add
    return found


KIND_ORDER = {"spec": 0, "plan": 1, "log": 2}


def topics(docs: list[schema.LibraryDoc], titles: dict[str, str], added: dict[str, int]):
    """The work by topic: each step's specs, plans and log posts, newest first, a day's in the
    order they were written, and the topic with the newest doc first."""
    by_step: dict[str, list[schema.LibraryDoc]] = {}
    for d in docs:
        by_step.setdefault(step_of(Path(d.path).name) or "other", []).append(d)

    def when(d: schema.LibraryDoc):
        # a doc git hasn't seen yet is the newest of its day
        return (d.date or "", added.get(d.path + ".md", 2**62), -KIND_ORDER.get(d.kind or "", 3))

    order = list(titles)
    sections = []
    for step, found in by_step.items():
        found.sort(key=when, reverse=True)
        sections.append(schema.LibrarySection(
            name=titles.get(step, "Other"), docs=found, group=TOPICS_GROUP,
            step=step if step in titles else None))  # fmt: skip

    def newest(s: schema.LibrarySection):
        return max(when(d) for d in s.docs), -order.index(s.step) if s.step in order else 0

    sections.sort(key=newest, reverse=True)
    return sections


def write_library(root, out) -> list[Path]:
    """library.json (the index) and library/<path>.json for every doc, with the files they
    point at copied under library/files/."""
    from pcs14.site.data import _write

    root, out = Path(root), Path(out)
    found = _docs(root)
    docs = {rel for _, rel in found}
    copied: set[str] = set()
    written, index = [], {}
    kinds = {rel: kind for kind, pattern in TOPICS for rel in
             (p.relative_to(root).as_posix() for p in root.glob(pattern))}  # fmt: skip
    for section, rel in found:
        text = (root / rel).read_text(encoding="utf-8")
        title = _title(text, rel)
        link, image = _rewriters(rel, docs, root, out, copied)
        note = superseded(text)
        page = schema.LibraryPage(
            schema_version=schema.SCHEMA_VERSION,
            path=route_of(rel),
            title=title,
            url=GITHUB + rel,
            html=markdown.to_html(text, link=link, image=image),
        )
        target = out / "library" / f"{route_of(rel)}.json"
        target.parent.mkdir(parents=True, exist_ok=True)
        written.append(_write(out, f"library/{route_of(rel)}", page))
        date = re.match(r"^(\d{4}-\d{2}-\d{2})", Path(rel).name)
        index.setdefault(section, []).append(
            schema.LibraryDoc(
                path=route_of(rel),
                title=title,
                section=section,
                url=GITHUB + rel,
                date=date.group(1) if date else None,
                kind=kinds.get(rel),
                superseded=note,
            )
        )
    for rel in sorted(copied):
        target = out / "library" / "files" / rel
        target.parent.mkdir(parents=True, exist_ok=True)
        shutil.copyfile(root / rel, target)
        written.append(target)
    readme = root / "README.md"
    titles = step_titles(readme.read_text(encoding="utf-8")) if readme.is_file() else {}
    sections = []
    for name, docs_in in index.items():
        if name == TOPICS_GROUP:
            sections += topics(docs_in, titles, _added(root))
        else:
            group = name if name in ABOUT else ""
            sections.append(schema.LibrarySection(name=name, docs=docs_in, group=group,
                                                  about=ABOUT.get(name, "")))  # fmt: skip
    # the work by topic after the build package, the folders and the notes after it
    fixed = [s for s in sections if s.group != TOPICS_GROUP]
    cut = next((i for i, s in enumerate(fixed) if s.name == "The repo's folders"), len(fixed))
    work = [s for s in sections if s.group == TOPICS_GROUP]
    if work:  # the group's words, once, on its first topic
        work[0].about = ABOUT[TOPICS_GROUP]
    sections = fixed[:cut] + work + fixed[cut:]
    library = schema.Library(schema_version=schema.SCHEMA_VERSION, sections=sections)
    written.append(_write(out, "library", library))
    return written


# --- the catalog --------------------------------------------------------------------------


def catalog_data(catalog) -> schema.Catalog:
    parts = []
    for part in sorted(catalog.all_parts(), key=lambda p: (p.type, p.id)):
        record = json.loads(part.model_dump_json(exclude_none=True))
        parts.append(
            schema.CatalogPart(
                id=part.id,
                type=part.type,
                maker=part.maker,
                model=part.model,
                mass_g=getattr(part, "mass_g", None),
                price_usd=part.price_usd,
                link=str(part.link) if part.link else None,
                record=record,
            )
        )
    return schema.Catalog(schema_version=schema.SCHEMA_VERSION, parts=parts)


# --- the data: the reports' own, and the site's ---------------------------------------------

REPORT_DATA = (
    ("sizing", "The sizing report's data", "docs/reports/sizing/sizing.json",
     "The sizing model's verdict, the build, every setup's checks, weight and speeds, the sweep "
     "of every build the catalog allows, and what extra weight costs."),
    ("cad", "The CAD report's data", "docs/reports/cad/cad.json",
     "Every combination's weight, balance and checks, every piece of the model, the printed "
     "parts, the wire lengths, the hardware, the existing CAD it used, and what's estimated."),
    ("electrical", "The electrical report's data", "docs/reports/electrical/electrical.json",
     "Every check in every combination and flight case, the heat through the burst, the safety "
     "switch's sims, every wire route and board, and what's estimated or unproven."),
    ("flight-sim", "The flight sim report's data", "docs/reports/flight-sim/flight-sim.json",
     "Every scenario in every combination, flown by PX4 and by my firmware, each grade with its "
     "numbers, the models, the flight times closing the loop, and what it can't prove."),
    ("modules", "The modules report's data", "docs/reports/modules/modules.json",
     "Step 6's runs, the chute's opening and its jolts, HaLow's range, the companion computer, "
     "the false-trigger replay, and what it can't prove."),
    ("smart", "The smart features report's data", "docs/reports/smart/smart.json",
     "Step 7's runs, self-tuning's fits, the Meshtastic relay, the object detection's boxes, "
     "and what it can't prove."),
    ("structure", "The structure report's data", "docs/reports/structure/structure.json",
     "The arm's beam math, its modes and what shakes them, the chute mount's joints, and what "
     "it can't prove."),
    ("package", "The build package's data", "docs/build/package.json",
     "Every line on the parts list with its price, link and fallback, each combination's "
     "totals, and what's still open."),
)  # fmt: skip
# the site's folders of data, and what's in each
SITE_FOLDERS = {
    "flights": "One run each, for its page to play back: the drone's path, its motors and its "
    "events, from the flight sim's logs.",
    "tunnel": "The wind tunnel's stills and each case's frames as JPEGs, and in tunnel/flow/ each "
    "case's flow moving, its particles and its slice as a loop.",
    "library": "Every doc rendered, one file each, and the pictures they show.",
    "raw": "Each report's own data file, whole.",
    "stills": "Each step's pictures, copied from its report.",
    "wiring": "The harness diagrams, as drawings.",
    "drone.glb": "The CAD's model of the full drone, thinned for the browser.",
}


def _holds(data) -> list[str]:
    if not isinstance(data, dict):
        return []
    return [f"{k} ({len(v)})" if isinstance(v, list) else k for k, v in data.items()]


def write_raw(root, out) -> list[Path]:
    """raw/<name>.json, each report's own data, whole. Their index is write_data_index's."""
    from pcs14.site.data import _write

    root, out = Path(root), Path(out)
    (out / "raw").mkdir(parents=True, exist_ok=True)
    written = []
    for name, _, rel, _ in REPORT_DATA:
        path = root / rel
        if path.is_file():
            data = json.loads(path.read_text(encoding="utf-8"))
            raw = schema.RawData(schema_version=schema.SCHEMA_VERSION, name=name, source=rel,
                                 data=data)  # fmt: skip
            written.append(_write(out, f"raw/{name}", raw))
    return written


def _size(path: Path) -> tuple[int, int]:
    """Bytes and files, a folder's all but the .js twins of its data."""
    if path.is_file():
        return path.stat().st_size, 1

    def twin(f: Path) -> bool:  # x.js beside x.json, or y.bin.js beside y.bin
        return f.suffix == ".js" and (f.with_suffix(".json").is_file() or f.stem.endswith(".bin"))

    files = [f for f in path.rglob("*") if f.is_file() and not twin(f)]
    return sum(f.stat().st_size for f in files), len(files)


def write_data_index(root, out) -> Path:
    """raw.json: each report's data with what it holds and its size, then every file and
    folder the site reads, from what's in `out` now: so it's written last, and again after the
    flights and the tunnel."""
    from pcs14.site.data import _write

    root, out = Path(root), Path(out)
    files = []
    for name, title, rel, about in REPORT_DATA:
        path = root / rel
        if path.is_file():
            data = json.loads(path.read_text(encoding="utf-8"))
            files.append(schema.RawFile(name=name, title=title, source=rel, url=GITHUB + rel,
                                        about=about, holds=_holds(data),
                                        size_bytes=path.stat().st_size))  # fmt: skip
    site = []
    for path in sorted(out.glob("*.json")):
        stem = path.stem
        shape = schema.FILES.get(stem)
        doc = (shape.__doc__ or "").split(":", 1)[-1] if shape else ""
        about = " ".join(doc.split()).strip()
        site.append(schema.SiteFile(name=path.name, about=about[:1].upper() + about[1:],
                                    size_bytes=path.stat().st_size, view=stem))  # fmt: skip
    for name, about in SITE_FOLDERS.items():
        path = out / name
        if path.exists():
            size, count = _size(path)
            site.append(schema.SiteFile(name=name + ("/" if path.is_dir() else ""), about=about,
                                        size_bytes=size, files=count))  # fmt: skip
    index = schema.RawIndex(schema_version=schema.SCHEMA_VERSION, files=files, site=site)
    return _write(out, "raw", index)


# --- the math -----------------------------------------------------------------------------

# the packages that do the math, in step order: (package, its name on the page, its step). The
# code that writes the reports, the site, the build package and the command line isn't math.
MATH = (
    ("sizing", "Sizing: thrust, power, the battery, flight time", "1"),
    ("cad", "The CAD: the shapes, the mass and the balance", "2"),
    ("electrical", "The wiring: currents, voltages, heat", "3"),
    ("flight", "The flight sim: the models, the scenarios and their grades", "4"),
    ("firmware", "My firmware and the safety monitor (C++)", "5"),
    ("safety", "The safety monitor's triggers", "5"),
    ("modules", "The modules: the chute, HaLow, the video", "6"),
    ("smart", "The smart features", "7"),
    ("structure", "Structure: beams and joints", "side track"),
    ("aero", "Aero: the wind tunnel's flow", "side track"),
)


def _signature(node) -> str:
    try:
        return f"{node.name}({ast.unparse(node.args)})"
    except (AttributeError, ValueError):
        return node.name


def _python(path: Path, rel: str, base: str = GITHUB) -> schema.MathModule:
    tree = ast.parse(path.read_text(encoding="utf-8"))
    items = []
    for node in tree.body:
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef)):
            doc = ast.get_docstring(node) or ""
            kind = "class" if isinstance(node, ast.ClassDef) else "function"
            sig = node.name if kind == "class" else _signature(node)
            items.append(
                schema.MathItem(name=node.name, kind=kind, signature=sig, doc=doc, line=node.lineno)
            )
            if isinstance(node, ast.ClassDef):
                for sub in node.body:
                    if isinstance(sub, (ast.FunctionDef, ast.AsyncFunctionDef)):
                        sub_doc = ast.get_docstring(sub)
                        if sub_doc:
                            items.append(
                                schema.MathItem(
                                    name=f"{node.name}.{sub.name}",
                                    kind="method",
                                    signature=_signature(sub),
                                    doc=sub_doc,
                                    line=sub.lineno,
                                )
                            )
    # the ones that explain themselves first, each group in the file's order
    items.sort(key=lambda i: (not i.doc, i.line))
    return schema.MathModule(
        path=rel,
        language="Python",
        doc=ast.get_docstring(tree) or "",
        url=base + rel,
        items=items,
    )


def _leading_comment(text: str) -> str:
    lines = []
    for line in text.splitlines():
        s = line.strip()
        if s.startswith("//"):
            lines.append(s[2:].strip())
        elif not s and not lines:
            continue
        else:
            break
    return "\n".join(lines)


def math_data(root, commit: str | None = None) -> schema.Math:
    """The math packages' modules, in step order, with links to the code pinned to `commit`
    (main without one)."""
    root = Path(root)
    base = GITHUB.replace("/blob/main/", f"/blob/{commit}/") if commit else GITHUB
    names = {key: (name, step) for key, name, step in MATH}
    packages: dict[str, list] = {}
    for path in sorted((root / "src" / "pcs14").rglob("*.py")):
        parts = path.relative_to(root / "src" / "pcs14").parts
        if len(parts) < 2 or parts[0] not in names:
            continue
        rel = path.relative_to(root).as_posix()
        module = _python(path, rel, base)
        if module.doc or module.items:
            packages.setdefault(parts[0], []).append(module)
    for path in sorted((root / "firmware").rglob("*")):
        if path.suffix not in (".hpp", ".cpp", ".h") or "tests" in path.parts:
            continue
        rel = path.relative_to(root).as_posix()
        doc = _leading_comment(path.read_text(encoding="utf-8", errors="replace"))
        if doc:
            packages.setdefault("firmware", []).append(
                schema.MathModule(path=rel, language="C++", doc=doc, url=base + rel, items=[])
            )
    order = [key for key, _, _ in MATH]
    return schema.Math(
        schema_version=schema.SCHEMA_VERSION,
        commit=commit,
        packages=[schema.MathPackage(name=names[k][0], key=k, step=names[k][1], modules=packages[k])
                  for k in order if k in packages],
    )  # fmt: skip


def write_everything(root, out, commit: str | None = None) -> list[Path]:
    """The library, the reports' raw data and the math, under `out`."""
    from pcs14.site.data import _write

    root, out = Path(root), Path(out)
    written = write_library(root, out)
    written += write_raw(root, out)
    written.append(_write(out, "math", math_data(root, commit)))
    return written
