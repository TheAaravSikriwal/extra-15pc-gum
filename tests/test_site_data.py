"""The project site's data (pcs14 site): what it writes, checked against the shapes the site
reads (site/schema, exported from pcs14.site.schema)."""

import json
import shutil
from pathlib import Path

import pytest

from pcs14.site import data, schema

ROOT = Path(__file__).resolve().parents[1]
REPORTS = ROOT / "docs" / "reports"


def test_the_index_says_what_was_found_and_what_wasnt(tmp_path):
    reports = tmp_path / "reports"
    (reports / "sizing").mkdir(parents=True)
    shutil.copy(REPORTS / "sizing" / "sizing.json", reports / "sizing" / "sizing.json")
    written = data.write_all(tmp_path / "out", reports, commit="abc1234")
    index = schema.Index.model_validate_json((tmp_path / "out" / "index.json").read_text())
    assert index.schema_version == schema.SCHEMA_VERSION and index.commit == "abc1234"
    assert index.reports["sizing"].found and index.reports["sizing"].verdict == "pass"
    assert not index.reports["cad"].found  # missing is listed, not an error
    assert sorted(p.name for p in written) == sorted(index.files + ["index.json"])


def test_the_spec_sheet_has_every_combination_with_the_reports_numbers():
    sizing = json.loads((REPORTS / "sizing" / "sizing.json").read_text(encoding="utf-8"))
    cad = json.loads((REPORTS / "cad" / "cad.json").read_text(encoding="utf-8"))
    sheet = data.spec_sheet(sizing, cad)
    assert [c.name for c in sheet.combinations] == [s["name"] for s in sizing["setups"]]
    base = sheet.combinations[0]
    assert base.mass_g == pytest.approx(sizing["setups"][0]["mass_g"])
    assert base.cad_mass_g == pytest.approx(cad["combinations"][0]["mass_g"])
    hover = next(c for c in base.checks if c.name == "Hover time")
    assert hover.nominal == pytest.approx(sizing["setups"][0]["checks"][0]["nominal"])
    roles = {p.role for p in sheet.parts}
    assert {"motor", "prop", "esc", "frame", "cell"} <= roles
    assert any(p.module == "V" for p in sheet.parts)  # the modules' parts, by module


def test_without_the_cad_the_spec_sheet_still_stands():
    sizing = json.loads((REPORTS / "sizing" / "sizing.json").read_text(encoding="utf-8"))
    sheet = data.spec_sheet(sizing, None)
    assert all(c.cad_mass_g is None for c in sheet.combinations)


def test_the_schema_files_are_the_models():
    """site/schema is what the site's TypeScript reads; it's exported from the models, and a
    stale copy fails here (pcs14 site --schema rewrites it)."""
    for name, model in schema.FILES.items():
        on_disk = json.loads((ROOT / "site" / "schema" / f"{name}.schema.json").read_text())
        assert on_disk == model.model_json_schema(), f"{name}: run pcs14 site --schema"


def test_a_file_from_another_schema_version_is_refused(tmp_path):
    path = tmp_path / "index.json"
    path.write_text(json.dumps({"schema_version": 999}))
    with pytest.raises(ValueError, match="pcs14 site"):
        data.load(path, schema.Index)


def test_the_command_writes_every_file_and_each_one_reads_back(tmp_path):
    from pcs14.cli import main

    out = tmp_path / "data"
    assert main(["site", "--reports", str(REPORTS), "--out", str(out)]) == 0
    index = data.load(out / "index.json", schema.Index)
    for name in index.files:
        data.load(out / name, schema.FILES[Path(name).stem])


CAD = {"pieces": [
    {"name": "frame", "kind": "frame", "module": "base", "mass_g": 343.0,
     "part_id": "iflight-nazgul-xl10-v6", "moving": False},
    {"name": "prop front left", "kind": "prop", "module": "base", "mass_g": 16.8,
     "part_id": "gemfan-1050x3", "moving": True},
    {"name": "wire battery leads", "kind": "wire", "module": "base", "mass_g": 30.0,
     "part_id": None, "moving": False},
]}  # fmt: skip
ELECTRICAL = {
    "routes": {"battery leads": ["lead.XT60.+ to esc.BAT.VBAT", "lead.XT60.- to esc.BAT.GND"]},
    "route_heating_share": {"base": {"hover": {"battery leads": 0.0641},
                                     "burst": {"battery leads": 0.31}}},
}  # fmt: skip


def test_the_parts_are_the_glbs_pieces_with_their_catalog_entries():
    sizing = json.loads((REPORTS / "sizing" / "sizing.json").read_text(encoding="utf-8"))
    sheet = data.spec_sheet(sizing, None)
    parts = data.parts(CAD, sheet)
    by_name = {p.name: p for p in parts.pieces}
    assert set(by_name) == {"frame", "prop front left", "wire battery leads"}
    assert by_name["prop front left"].catalog.maker == "Gemfan"
    assert by_name["wire battery leads"].catalog is None


def test_each_route_names_its_wires_ends_and_how_hard_it_works():
    wires = data.wires(ELECTRICAL)
    (route,) = wires.routes
    assert route.node == "wire battery leads"  # the GLB's name for it
    assert route.wires[0].ends == ["lead.XT60.+", "esc.BAT.VBAT"]
    assert route.heating_share["base"]["burst"] == pytest.approx(0.31)


def test_reports_from_before_the_site_skip_those_files(tmp_path):
    """cad.json and electrical.json from before 2026-10-20 have no pieces or routes yet."""
    reports = tmp_path / "reports"
    for name in ("sizing/sizing.json", "cad/cad.json", "electrical/electrical.json"):
        (reports / name).parent.mkdir(parents=True, exist_ok=True)
        raw = json.loads((REPORTS / name).read_text(encoding="utf-8"))
        raw.pop("pieces", None), raw.pop("routes", None)
        (reports / name).write_text(json.dumps(raw))
    data.write_all(tmp_path / "out", reports)
    index = data.load(tmp_path / "out" / "index.json", schema.Index)
    assert "parts.json" not in index.files and "wires.json" not in index.files
    assert "spec.json" in index.files


def test_every_piece_in_the_glb_has_a_part_and_the_other_way_round():
    glb = ROOT / "outputs" / "cad" / "drone.glb"
    cad = json.loads((REPORTS / "cad" / "cad.json").read_text(encoding="utf-8"))
    if not glb.is_file() or "pieces" not in cad:
        pytest.skip("needs pcs14 cad run since 2026-10-20 (its GLB and the pieces in cad.json)")
    nodes = set(data.glb_nodes(glb))
    assert nodes == {p["name"] for p in cad["pieces"]}
    electrical = json.loads((REPORTS / "electrical" / "electrical.json").read_text("utf-8"))
    if "routes" in electrical:  # and every route the wires take is drawn in it
        assert {r.node for r in data.wires(electrical).routes} <= nodes


def test_each_file_also_comes_as_a_script_for_pages_opened_from_disk(tmp_path):
    """Browsers won't fetch() from a page opened as file://, but they will run a script tag,
    so every data file is also written as one that hands its data to the page."""
    data.write_all(tmp_path, REPORTS)
    for name in ["index.json", *data.load(tmp_path / "index.json", schema.Index).files]:
        script = (tmp_path / name.replace(".json", ".js")).read_text(encoding="utf-8")
        prefix = f'(window.pcs14Data = window.pcs14Data || {{}})["{name}"] = '
        assert script.startswith(prefix) and script.rstrip().endswith(";")
        body = script[len(prefix) :].rstrip().rstrip(";")
        assert json.loads(body) == json.loads((tmp_path / name).read_text(encoding="utf-8"))
