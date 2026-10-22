"""`pcs14 site`: every step's report into the site's data files.

It reads the reports' own data files (docs/reports/*/*.json), so what the site shows is
exactly what the reports say. Three things read the design itself, because they are the
design: the library and the catalog (pcs14.site.library) and every wire in 3D
(pcs14.site.wires3d). A report that isn't there is
listed as missing in index.json and its files are skipped: the site grows as the steps do.
"""

import json
import shutil
import struct
from datetime import date
from pathlib import Path

from pcs14.site import schema

REPORTS = {  # each report the site reads, by name, and its data file under the reports folder
    "sizing": "sizing/sizing.json",
    "cad": "cad/cad.json",
    "electrical": "electrical/electrical.json",
    "flight-sim": "flight-sim/flight-sim.json",
    "modules": "modules/modules.json",
    "smart": "smart/smart.json",
    "structure": "structure/structure.json",
}


def _read(reports: Path, name: str) -> dict | None:
    path = Path(reports) / REPORTS[name]
    return json.loads(path.read_text(encoding="utf-8")) if path.is_file() else None


def _part(item: dict, role: str, module: str | None = None, count: int = 1) -> schema.Part:
    return schema.Part(role=role, module=module, id=item["id"], maker=item["maker"],
                       model=item["model"], mass_g=item["mass_g"], price_usd=item.get("price_usd"),
                       link=item.get("link"), count=count)  # fmt: skip


def _shown(check: dict) -> dict:
    """A check's numbers as the sizing report prints them, rounded toward failing."""
    from pcs14.report.formatting import fmt_limit, fmt_value, with_unit

    unit, high = check["unit"], check.get("higher_is_better", True)
    out = {"shown": with_unit(fmt_value(check["nominal"], unit, high), unit)}
    if check.get("pessimistic") is not None:
        out["shown_pessimistic"] = with_unit(fmt_value(check["pessimistic"], unit, high), unit)
    if check.get("limit") is not None:
        side = "at least" if high else "at most"
        out["shown_limit"] = f"{side} {with_unit(fmt_limit(check['limit'], unit), unit)}"
    if check.get("margin") is not None:
        out["shown_margin"] = f"{check['margin'] * 100:+.0f}%"
    return out


def _numbers(s: dict, c: dict | None) -> list[list[str]]:
    """A combination's key numbers, worded and rounded as the sizing report has them."""
    from pcs14.report.formatting import fmt_value

    weight = f"{s['mass_g']:.0f} g"
    if s["growth_margin_g"]:
        weight += f", with {s['growth_margin_g']:.0f} g of growth margin"
    rows = [["Weight, sizing model", weight]]
    if c:
        cad = f"{c['mass_g']:.0f} g"
        rows.append(["Weight, CAD", cad + (", without the margin" if s["growth_margin_g"] else "")])
    for check in s["checks"]:
        shown = _shown(check)
        value = shown["shown"]
        if "shown_pessimistic" in shown:
            value += f" ({shown['shown_pessimistic']} pessimistic)"
        rows.append([check["name"], value])
    top = s["top_speed_kmh"]
    speed = {k: f"{v:.0f}" for k, v in top.items()}  # the report's own rounding, for these
    rows.append(["Top speed", f"{speed.get('full')} km/h on a full pack, {speed.get('half')} at "
                 f"half charge, {speed.get('reserve')} at the reserve"])  # fmt: skip
    minutes = fmt_value(s["least_power_minutes"], "min", True)
    rows.append(["Cheapest speed", f"{s['least_power_speed_ms']:.1f} m/s, for {minutes} min of "
                 "cruise (the longest it can stay up)"])  # fmt: skip
    return rows


def spec_sheet(sizing: dict, cad: dict | None) -> schema.SpecSheet:
    """The spec sheet: each combination's weights, checks and speeds from the sizing report,
    worded and rounded as the report has them, what its weight is made of, and the CAD's own
    weight and balance next to them when the CAD report is there."""
    by_setup = {c["setup"]: c for c in (cad or {}).get("combinations", [])}
    combinations = []
    for s in sizing["setups"]:
        c = by_setup.get(s["name"])
        balance = None
        if c:
            balance = schema.Balance(passed=c["passed"], trim_x_mm=c["trim_x_mm"],
                                     center_of_gravity_mm=c["center_of_gravity_mm"],
                                     busiest_motor_extra=c["busiest_motor_extra"],
                                     inertia_kg_m2=c["inertia_kg_m2"])  # fmt: skip
        combinations.append(schema.Combination(
            name=s["name"], modules=s["modules"], verdict=s["verdict"],
            required=s.get("required", False), mass_g=s["mass_g"],
            growth_margin_g=s["growth_margin_g"],
            cad_mass_g=c["mass_g"] if c else None,
            center_of_gravity_mm=c["center_of_gravity_mm"] if c else None,
            checks=[schema.Check(**{k: v for k, v in check.items() if k != "margin"},
                                 **_shown(check)) for check in s["checks"]],
            top_speed_kmh=s["top_speed_kmh"], least_power_speed_ms=s["least_power_speed_ms"],
            least_power_minutes=s["least_power_minutes"],
            mass_lines=[schema.MassLine(**line) for line in s.get("mass_lines", [])],
            balance=balance, numbers=_numbers(s, c),
        ))  # fmt: skip
    b = sizing["build"]
    pack = b["pack"]
    parts = [
        _part(b["motor"], "motor", count=4),
        _part(b["prop"], "prop", count=4),
        _part(b["esc"], "esc"),
        _part(b["frame"], "frame"),
        _part(pack["cell"], "cell", count=pack["series"] * pack["parallel"]),
    ]
    parts += [_part(item, item["id"]) for item in b.get("components", [])]
    for module, items in b.get("modules", {}).items():
        parts += [_part(item, item["id"], module) for item in items]
    cell = pack["cell"]
    return schema.SpecSheet(
        schema_version=schema.SCHEMA_VERSION, sizing_case=sizing["sizing_case"],
        verdict=sizing["verdict"], targets=sizing["targets"], combinations=combinations,
        parts=parts,
        pack=schema.Pack(cell=f"{cell['maker']} {cell['model']}", cell_id=cell["id"],
                         series=pack["series"], parallel=pack["parallel"],
                         capacity_mah=pack["capacity_mah"], resistance_mohm=pack["resistance_mohm"],
                         mass_g=pack["mass_g"]),
    )  # fmt: skip


def parts(cad: dict, sheet: schema.SpecSheet, glb: str = "drone.glb") -> schema.Parts:
    """Every piece the CAD exported, with the spec sheet's catalog entry for a bought one."""
    catalog = {p.id: p for p in sheet.parts}
    pieces = [schema.Piece(**p, catalog=catalog.get(p["part_id"])) for p in cad["pieces"]]
    return schema.Parts(schema_version=schema.SCHEMA_VERSION, glb=glb, pieces=pieces)


def wires(electrical: dict) -> schema.Wires:
    """Each CAD route: its wires and their ends, and the hardest-working wire's share of its
    heating limit in every combination and case."""
    shares = electrical.get("route_heating_share", {})
    routes = []
    for name, labels in electrical["routes"].items():
        heating = {setup: {case: by_route[name] for case, by_route in cases.items()
                           if name in by_route}
                   for setup, cases in shares.items()}  # fmt: skip
        routes.append(schema.Route(
            name=name, node=f"wire {name}",
            wires=[schema.Wire(label=label, ends=label.split(" to ")) for label in labels],
            heating_share=heating,
        ))  # fmt: skip
    return schema.Wires(schema_version=schema.SCHEMA_VERSION, routes=routes)


def glb_nodes(path) -> list[str]:
    """The pieces in a GLB, read from its JSON chunk (glTF 2.0's binary layout): its named
    nodes with no named node above them. Below a piece are the named parts of its look (a
    board's "chips" and "pins"), which aren't pieces of their own."""
    raw = Path(path).read_bytes()
    length, kind = struct.unpack("<I4s", raw[12:20])
    if raw[:4] != b"glTF" or kind != b"JSON":
        raise ValueError(f"{path} isn't a GLB")
    nodes = json.loads(raw[20 : 20 + length]).get("nodes", [])
    parent = {child: k for k, n in enumerate(nodes) for child in n.get("children", [])}

    def under_a_named_one(k: int) -> bool:
        while k in parent:
            k = parent[k]
            if nodes[k].get("name"):
                return True
        return False

    return [n["name"] for k, n in enumerate(nodes) if n.get("name") and not under_a_named_one(k)]


def _write(out: Path, name: str, model) -> Path:
    path = out / f"{name}.json"
    path.parent.mkdir(parents=True, exist_ok=True)
    text = model.model_dump_json(indent=1)
    path.write_bytes((text + "\n").encode("utf-8"))  # LF anywhere
    # and the same as a script: a page opened from disk (file://) can't fetch(), but it can run
    # a script tag, which hands the data over on window.pcs14Data
    script = f'(window.pcs14Data = window.pcs14Data || {{}})["{name}.json"] = {text};\n'
    (out / f"{name}.js").write_bytes(script.encode("utf-8"))
    return path


def wiring(electrical: dict, reports, out) -> schema.Wiring:
    """Every board's pins from electrical.json, and its harness diagrams and schematic copied
    under `out`/wiring."""
    from pcs14.site.steps import GITHUB

    reports, out = Path(reports), Path(out)
    folder = reports / "electrical"
    (out / "wiring").mkdir(parents=True, exist_ok=True)
    harnesses = []
    for file in electrical.get("files", []):
        if file.startswith("harnesses/") and (folder / file).is_file():
            target = f"wiring/{Path(file).name}"
            shutil.copyfile(folder / file, out / target)
            harnesses.append(schema.Harness(name=Path(file).stem.replace("-", " "), file=target))
    schematic = None
    for export in electrical.get("exports", []):
        drawn = reports.resolve().parent.parent / export
        if export.endswith(".svg") and drawn.is_file():
            shutil.copyfile(drawn, out / "wiring" / "schematic.svg")
            schematic = "wiring/schematic.svg"
    boards = [schema.BoardPins(name=name, **b) for name, b in electrical["boards"].items()]
    kicad = GITHUB + "docs/reports/electrical/kicad/electrical.kicad_sch"
    return schema.Wiring(schema_version=schema.SCHEMA_VERSION, boards=boards,
                         harnesses=harnesses, schematic=schematic, kicad=kicad)  # fmt: skip


GUIDES = (
    ("The parts list", "parts", "Every part with its link, the day it was checked and a fallback, "
     "as a table and a CSV."),
    ("The assembly guide", "assembly", "How it goes together, step by step, each step pictured "
     "from the CAD with its new parts in spearmint."),
    ("The wiring guide", "wiring", "Every wire once, under its harness, with its gauge and cut "
     "length, and the checks with a meter before power."),
    ("The firmware", "firmware", "PX4 on the ARK FPV first, then my firmware, and how each is "
     "set up for this drone."),
    ("The test plans", "tests", "Bench checks first, props off, then the first flights, tethered "
     "first; each check says what passes."),
    ("The legal checklist", "legal", "Each US rule, what it means for this drone, and where it "
     "lives: the limits profile, a part, or me."),
)  # fmt: skip


def build_data(package: dict) -> schema.Build:
    """build.json from the build package's own data file, its guides on the site's library."""
    return schema.Build(
        schema_version=schema.SCHEMA_VERSION,
        generated=package["generated"],
        totals=[schema.BuildTotal(**t) for t in package["totals"]],
        lines=[schema.BuildLine(**x) for x in package["lines"]],
        guides=[
            schema.BuildGuide(name=n, url=f"#/library/docs/build/{f}", about=about)
            for n, f, about in GUIDES
        ],  # fmt: skip
        open=package.get("open", []),
    )


# the design's own files, where the parts it uses are named by their catalog ids
DESIGN_FILES = ("build.yaml", "cad.yaml", "electrical.yaml", "targets.yaml")


def _key(maker: str, model: str) -> tuple[str, str]:
    return maker.strip().lower(), model.strip().lower()


def parts_list(package: dict, catalog: schema.Catalog, design: str = "") -> schema.PartsList:
    """Everything that goes on the drone, from the build package, each line with its catalog
    entry where it has one (matched by maker and model); the catalog entries the design uses
    (a line's, or one the design files name); and the rest of the catalog, the alternatives."""
    import re

    by_key = {_key(p.maker, p.model): p for p in catalog.parts}
    named = {p.id for p in catalog.parts
             if re.search(rf"(?<![\w-]){re.escape(p.id)}(?![\w-])", design)}  # fmt: skip
    lines, used = [], {p.id: p for p in catalog.parts if p.id in named}
    for x in package["lines"]:
        part = by_key.get(_key(x["maker"], x["model"]))
        if part is not None:
            used[part.id] = part
        lines.append(schema.PartsLine(**{k: x.get(k) for k in schema.PartsLine.model_fields
                                         if k in x and x.get(k) is not None},
                                      catalog_id=part.id if part else None,
                                      mass_g=part.mass_g if part else None))  # fmt: skip
    alternatives = [p for p in catalog.parts if p.id not in used]
    return schema.PartsList(schema_version=schema.SCHEMA_VERSION, generated=package["generated"],
                            lines=lines, used=list(used.values()),
                            alternatives=alternatives)  # fmt: skip


def shape_of(name: str):
    """The shape of a data file, by its path in the data folder: library/... is one doc,
    raw/... one report's data, and the rest by their own names."""
    if name.startswith("library/"):
        return schema.FILES["library-page"]
    if name.startswith("raw/"):
        return schema.FILES["raw-data"]
    return schema.FILES[Path(name).stem]


def write_all(out, reports, commit: str | None = None, today: str | None = None) -> list[Path]:
    """Writes every data file the reports allow, then index.json; returns the paths."""
    out, reports = Path(out), Path(reports)
    out.mkdir(parents=True, exist_ok=True)
    found = {name: _read(reports, name) for name in REPORTS}
    written = []
    sheet = None
    if found["sizing"] is not None:
        sheet = spec_sheet(found["sizing"], found["cad"])
        written.append(_write(out, "spec", sheet))
    # reports from before the site have no pieces or routes yet: those files wait for a rerun
    if sheet is not None and found["cad"] is not None and "pieces" in found["cad"]:
        written.append(_write(out, "parts", parts(found["cad"], sheet)))
    if found["electrical"] is not None and "routes" in found["electrical"]:
        written.append(_write(out, "wires", wires(found["electrical"])))
    if found["electrical"] is not None and "boards" in found["electrical"]:
        written.append(_write(out, "wiring", wiring(found["electrical"], reports, out)))
    # every wire pin to pin, for the drone view, from the design beside the docs
    design = reports.resolve().parent.parent / "design"
    if (design / "electrical.yaml").is_file():
        from pcs14.site.wires3d import wires3d

        written.append(_write(out, "wires3d", wires3d(design)))
    # what the sims can't prove
    docs = reports.resolve().parent
    if (docs / "decisions.md").is_file():
        from pcs14.site.unproven import unproven_data

        written.append(_write(out, "unproven", unproven_data(docs)))
    # a page per step, from the README's plan beside the docs the reports are in
    readme = reports.resolve().parent.parent / "README.md"
    if readme.is_file():
        from pcs14.site.steps import steps_data

        written.append(_write(out, "steps", steps_data(readme, reports.resolve().parent, out)))
    # everything else: every doc, every part, every report's data, and the math
    from pcs14.site.library import write_everything

    written += write_everything(docs.parent, out, commit)
    # the build package, when pcs14 package has written it
    package = docs / "build" / "package.json"
    if package.is_file():
        built = json.loads(package.read_text("utf-8"))
        written.append(_write(out, "build", build_data(built)))
        # and what goes on the drone, with its catalog entries, for the parts page
        catalog = docs.parent / "design" / "catalog"
        if catalog.is_dir():
            from pcs14.catalog import load_catalog
            from pcs14.site.library import catalog_data

            folder = docs.parent / "design"
            design = "\n".join((folder / name).read_text(encoding="utf-8")
                               for name in DESIGN_FILES if (folder / name).is_file())  # fmt: skip
            listed = parts_list(built, catalog_data(load_catalog(catalog)), design)
            written.append(_write(out, "parts-list", listed))
    index = schema.Index(
        schema_version=schema.SCHEMA_VERSION,
        generated=today or date.today().isoformat(),
        commit=commit,
        reports={
            name: schema.ReportFound(
                file=REPORTS[name],
                found=d is not None,
                generated=(d or {}).get("generated"),
                verdict=(d or {}).get("verdict"),
            )  # fmt: skip
            for name, d in found.items()
        },
        # the data, not the pictures, by their paths in the data folder
        files=[p.relative_to(out).as_posix() for p in written if p.suffix == ".json"],
    )
    written.append(_write(out, "index", index))
    # last, the index of every data file, with its size
    from pcs14.site.library import write_data_index

    return [*written, write_data_index(docs.parent, out)]


def load(path, shape):
    """A data file, read back through its shape; refuses one from another schema version."""
    raw = json.loads(Path(path).read_text(encoding="utf-8"))
    version = raw.get("schema_version")
    if version != schema.SCHEMA_VERSION:
        raise ValueError(
            f"{path} is schema version {version}, not {schema.SCHEMA_VERSION}: rerun pcs14 site"
        )
    return shape.model_validate(raw)


def write_schema(folder) -> list[Path]:
    """The models as JSON Schema, for the site's TypeScript (site/schema)."""
    folder = Path(folder)
    folder.mkdir(parents=True, exist_ok=True)
    out = []
    for name, model in schema.FILES.items():
        path = folder / f"{name}.schema.json"
        path.write_bytes((json.dumps(model.model_json_schema(), indent=1) + "\n").encode())
        out.append(path)
    return out
