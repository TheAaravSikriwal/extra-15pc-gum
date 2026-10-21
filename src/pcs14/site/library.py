"""Everything else, for the site: every Markdown doc in the repo rendered (the library), every
catalog part with every field (the catalog), every report's own data file (the data), and how
each number is worked out, from the code's own explanations (the math).

Links between docs stay on the site (#/library/docs/log/x, an anchor after a ~), pictures and
small files the docs point at are copied beside the data, and anything else points at GitHub.
"""

import ast
import json
import posixpath
import re
import shutil
from pathlib import Path

from pcs14.site import markdown, schema
from pcs14.site.steps import GITHUB

# the library's sections, in order: (name, the repo paths or globs that go in it)
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
            "CLAUDE.md",
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
    ("The log", ("docs/log/*.md",)),
    ("Specs", ("docs/specs/*.md",)),
    ("Plans", ("docs/plans/*.md",)),
    ("Machines and setup", ("docs/setup-pc.md", "docs/machines/*.md", "scripts/README.md")),
    (
        "The rest of the repo",
        (
            "design/README.md",
            "design/catalog/README.md",
            "design/validation/README.md",
            "cad/README.md",
            "aero/README.md",
            "sim/README.md",
            "explore/README.md",
            "media/README.md",
        ),
    ),
)
COPIED = (".png", ".jpg", ".jpeg", ".gif", ".svg", ".csv", ".txt")  # files the docs point at
REPORT_DATA = (
    ("sizing", "The sizing model", "docs/reports/sizing/sizing.json"),
    ("cad", "The CAD", "docs/reports/cad/cad.json"),
    ("electrical", "The wiring", "docs/reports/electrical/electrical.json"),
    ("flight-sim", "The flight sim", "docs/reports/flight-sim/flight-sim.json"),
    ("modules", "The modules in sim", "docs/reports/modules/modules.json"),
    ("smart", "The smart features", "docs/reports/smart/smart.json"),
    ("structure", "Structure", "docs/reports/structure/structure.json"),
    ("package", "The build package", "docs/build/package.json"),
)


def _docs(root: Path) -> list[tuple[str, str]]:
    """(section, repo path) for every doc, each once, in the sections' order."""
    seen, out = set(), []
    for section, patterns in SECTIONS:
        for pattern in patterns:
            found = sorted(root.glob(pattern)) if "*" in pattern else [root / pattern]
            for path in found:
                rel = path.relative_to(root).as_posix()
                if path.is_file() and rel not in seen:
                    seen.add(rel)
                    out.append((section, rel))
    return out


def _title(text: str, rel: str) -> str:
    m = re.search(r"^# (.+)$", text, re.M)
    return m.group(1).strip() if m else Path(rel).stem.replace("-", " ")


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


def write_library(root, out) -> list[Path]:
    """library.json (the index) and library/<path>.json for every doc, with the files they
    point at copied under library/files/."""
    from pcs14.site.data import _write

    root, out = Path(root), Path(out)
    found = _docs(root)
    docs = {rel for _, rel in found}
    copied: set[str] = set()
    written, index = [], {}
    for section, rel in found:
        text = (root / rel).read_text(encoding="utf-8")
        title = _title(text, rel)
        link, image = _rewriters(rel, docs, root, out, copied)
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
            )
        )
    for rel in sorted(copied):
        target = out / "library" / "files" / rel
        target.parent.mkdir(parents=True, exist_ok=True)
        shutil.copyfile(root / rel, target)
        written.append(target)
    library = schema.Library(
        schema_version=schema.SCHEMA_VERSION,
        sections=[schema.LibrarySection(name=n, docs=d) for n, d in index.items()],
    )
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


# --- the reports' own data ----------------------------------------------------------------


def write_raw(root, out) -> list[Path]:
    from pcs14.site.data import _write

    root, out = Path(root), Path(out)
    (out / "raw").mkdir(parents=True, exist_ok=True)
    files, written = [], []
    for name, title, rel in REPORT_DATA:
        path = root / rel
        if not path.is_file():
            continue
        data = json.loads(path.read_text(encoding="utf-8"))
        written.append(
            _write(
                out,
                f"raw/{name}",
                schema.RawData(
                    schema_version=schema.SCHEMA_VERSION, name=name, source=rel, data=data
                ),
            )
        )
        files.append(schema.RawFile(name=name, title=title, source=rel, url=GITHUB + rel))
    written.append(
        _write(out, "raw", schema.RawIndex(schema_version=schema.SCHEMA_VERSION, files=files))
    )
    return written


# --- the math -----------------------------------------------------------------------------

PACKAGE_NAMES = {
    "sizing": "Sizing: thrust, power, the battery, flight time",
    "catalog": "The catalog's formats",
    "cad": "The CAD",
    "electrical": "The wiring: currents, voltages, heat",
    "flight": "The flight sim",
    "safety": "The safety monitor's triggers",
    "modules": "The modules: the chute, HaLow, video",
    "smart": "The smart features",
    "structure": "Structure",
    "aero": "Aero",
    "package": "The build package",
    "ground": "The ground station",
    "site": "The site",
    "report": "The charts",
    "viz": "Replays",
}


def _signature(node) -> str:
    try:
        return f"{node.name}({ast.unparse(node.args)})"
    except (AttributeError, ValueError):
        return node.name


def _python(path: Path, rel: str) -> schema.MathModule:
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
    return schema.MathModule(
        path=rel,
        language="Python",
        doc=ast.get_docstring(tree) or "",
        url=GITHUB + rel,
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


def math_data(root) -> schema.Math:
    root = Path(root)
    packages: dict[str, list] = {}
    for path in sorted((root / "src" / "pcs14").rglob("*.py")):
        rel = path.relative_to(root).as_posix()
        parts = path.relative_to(root / "src" / "pcs14").parts
        package = parts[0] if len(parts) > 1 else "pcs14"
        module = _python(path, rel)
        if module.doc or module.items:
            packages.setdefault(package, []).append(module)
    for path in sorted((root / "firmware").rglob("*")):
        if path.suffix not in (".hpp", ".cpp", ".h") or "tests" in path.parts:
            continue
        rel = path.relative_to(root).as_posix()
        doc = _leading_comment(path.read_text(encoding="utf-8", errors="replace"))
        if doc:
            packages.setdefault("firmware", []).append(
                schema.MathModule(path=rel, language="C++", doc=doc, url=GITHUB + rel, items=[])
            )
    names = {
        **PACKAGE_NAMES,
        "pcs14": "The command line and its helpers",
        "firmware": "My firmware and the safety monitor (C++)",
    }
    order = list(PACKAGE_NAMES) + ["firmware", "pcs14"]
    keyed = sorted(packages.items(), key=lambda kv: order.index(kv[0]) if kv[0] in order else 99)
    return schema.Math(
        schema_version=schema.SCHEMA_VERSION,
        packages=[schema.MathPackage(name=names.get(k, k), key=k, modules=v) for k, v in keyed],
    )


def write_everything(root, out) -> list[Path]:
    """The library, the catalog, the raw data and the math, under `out`."""
    from pcs14.catalog import load_catalog
    from pcs14.site.data import _write

    root, out = Path(root), Path(out)
    written = write_library(root, out)
    catalog = root / "design" / "catalog"
    if catalog.is_dir():
        written.append(_write(out, "catalog", catalog_data(load_catalog(catalog))))
    written += write_raw(root, out)
    written.append(_write(out, "math", math_data(root)))
    return written
