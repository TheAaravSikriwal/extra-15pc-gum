"""`pcs14 site`: every step's report into the site's data files.

It only reads the reports' own data files (docs/reports/*/*.json), never the design or the
CAD, so what the site shows is exactly what the reports say. A report that isn't there is
listed as missing in index.json and its files are skipped: the site grows as the steps do.
"""

import json
import struct
from datetime import date
from pathlib import Path

from pcs14.site import schema

REPORTS = {  # each report the site reads, by name, and its data file under the reports folder
    "sizing": "sizing/sizing.json",
    "cad": "cad/cad.json",
    "electrical": "electrical/electrical.json",
    "flight-sim": "flight-sim/flight-sim.json",
}


def _read(reports: Path, name: str) -> dict | None:
    path = Path(reports) / REPORTS[name]
    return json.loads(path.read_text(encoding="utf-8")) if path.is_file() else None


def _part(item: dict, role: str, module: str | None = None, count: int = 1) -> schema.Part:
    return schema.Part(role=role, module=module, id=item["id"], maker=item["maker"],
                       model=item["model"], mass_g=item["mass_g"], price_usd=item.get("price_usd"),
                       link=item.get("link"), count=count)  # fmt: skip


def spec_sheet(sizing: dict, cad: dict | None) -> schema.SpecSheet:
    """The spec sheet: each combination's weights, checks and speeds from the sizing report,
    the CAD's own weight and balance next to them when the CAD report is there."""
    by_setup = {c["setup"]: c for c in (cad or {}).get("combinations", [])}
    combinations = []
    for s in sizing["setups"]:
        c = by_setup.get(s["name"])
        combinations.append(schema.Combination(
            name=s["name"], modules=s["modules"], verdict=s["verdict"], mass_g=s["mass_g"],
            growth_margin_g=s["growth_margin_g"],
            cad_mass_g=c["mass_g"] if c else None,
            center_of_gravity_mm=c["center_of_gravity_mm"] if c else None,
            checks=[schema.Check(**{k: v for k, v in check.items() if k != "margin"})
                    for check in s["checks"]],
            top_speed_kmh=s["top_speed_kmh"], least_power_speed_ms=s["least_power_speed_ms"],
            least_power_minutes=s["least_power_minutes"],
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
    return schema.SpecSheet(
        schema_version=schema.SCHEMA_VERSION, sizing_case=sizing["sizing_case"],
        verdict=sizing["verdict"], targets=sizing["targets"], combinations=combinations,
        parts=parts,
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
    """The named nodes in a GLB, read from its JSON chunk (glTF 2.0's binary layout)."""
    raw = Path(path).read_bytes()
    length, kind = struct.unpack("<I4s", raw[12:20])
    if raw[:4] != b"glTF" or kind != b"JSON":
        raise ValueError(f"{path} isn't a GLB")
    gltf = json.loads(raw[20 : 20 + length])
    return [n["name"] for n in gltf.get("nodes", []) if n.get("name")]


def _write(out: Path, name: str, model) -> Path:
    path = out / f"{name}.json"
    text = model.model_dump_json(indent=1)
    path.write_bytes((text + "\n").encode("utf-8"))  # LF anywhere
    # and the same as a script: a page opened from disk (file://) can't fetch(), but it can run
    # a script tag, which hands the data over on window.pcs14Data
    script = f'(window.pcs14Data = window.pcs14Data || {{}})["{name}.json"] = {text};\n'
    (out / f"{name}.js").write_bytes(script.encode("utf-8"))
    return path


def hero(view, out, margin_px: int = 48) -> Path:
    """The home page's drone: the CAD's three-quarter view without its post header and footer,
    trimmed to the drone with a margin of the background around it."""
    import numpy as np
    from PIL import Image

    out = Path(out)
    out.mkdir(parents=True, exist_ok=True)
    with Image.open(view) as image:
        picture = np.asarray(image.convert("RGB"))
    h, w = picture.shape[:2]
    background = picture[h // 2, 2].astype(int)  # the left edge, halfway down
    top, bottom = int(h * 0.18), int(h * 0.92)  # under the title, over the footer
    different = np.abs(picture[top:bottom].astype(int) - background).sum(axis=2) > 24
    rows, cols = np.nonzero(different)
    if rows.size == 0:
        y0, y1, x0, x1 = top, bottom, 0, w
    else:
        y0, y1 = top + rows.min() - margin_px, top + rows.max() + margin_px
        x0, x1 = cols.min() - margin_px, cols.max() + margin_px
    y0, y1, x0, x1 = max(y0, top), min(y1, bottom), max(x0, 0), min(x1, w)
    path = out / "hero.png"
    Image.fromarray(picture[y0:y1, x0:x1]).save(path, optimize=True)
    return path


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
    # the home page's drone
    view = reports / "cad" / "views" / "three-quarter.png"
    if view.is_file():
        written.append(hero(view, out))
    # what the sims can't prove, front and center
    docs = reports.resolve().parent
    if (docs / "decisions.md").is_file():
        from pcs14.site.unproven import unproven_data

        written.append(_write(out, "unproven", unproven_data(docs)))
    # a page per step, from the README's plan beside the docs the reports are in
    readme = reports.resolve().parent.parent / "README.md"
    if readme.is_file():
        from pcs14.site.steps import steps_data

        written.append(_write(out, "steps", steps_data(readme, reports.resolve().parent, out)))
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
        files=[p.name for p in written if p.suffix == ".json"],  # the data, not the pictures
    )
    return [*written, _write(out, "index", index)]


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
