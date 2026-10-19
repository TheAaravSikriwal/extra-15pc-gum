"""The wiring's real weight, from the connection list, and closing the loop: it goes into the
catalog's wiring entries (one for Base, one for each module), marked as worked out from the list,
along with the main path's resistance into the build."""

import shutil
from pathlib import Path

import pytest
import yaml

from electrical_parts import LISTED, PARTS, connector, part
from pcs14.electrical import mass
from pcs14.electrical.model import ConnectionList
from pcs14.electrical.validate import Wiring

ROOT = Path(__file__).resolve().parents[1]
GH = 0.05  # g a position, both halves, the made-up family's like the real one
XT60 = 3.29  # g, one half

FAMILIES = {
    "t-gh": part("t-gh", {"rating": {"continuous_a": 1.0}}, mass_g=GH),
    "t-xt60": part("t-xt60", {"rating": {"continuous_a": 30.0}}, mass_g=XT60),
    "t-lead": part(
        "t-lead",
        {"connectors": [connector("XT60", "+ power", "- ground", family="t-xt60")]},
        mass_g=45,
    ),
    "t-servo": part(
        "t-servo",
        {
            "connectors": [connector("pads", "V+ power max_volts=6", "GND ground", family="pads")],
            "draws": [{"pin": "pads.V+", "min_v": 4, "max_v": 6, "typical_a": 0.1, "worst_a": 1}],
        },
    ),
}
ALL = {**PARTS, **FAMILIES}
LIST = {**LISTED, "t-lead": {"base"}, "t-servo": {"P"}, "t-gh": {"base"}, "t-xt60": {"base"}}


def wire(a, b, awg=18, route=None, length_mm=None, harness="h"):
    run = {"ends": [a, b], "wire": "t-wire", "awg": awg, "harness": harness}
    if route:
        run["route"] = route
    else:
        run["length_mm"] = length_mm
    return run


def made_up():
    """A lead with an XT60, a regulator on a JST plug, and a servo in P on pads."""
    data = {
        "boards": {
            "lead": {"part": "t-lead"},
            "reg": {"part": "t-reg"},
            "servo": {"part": "t-servo"},
        },
        "wires": [
            wire("lead.XT60.+", "reg.J.VIN", route="leads"),  # 18 AWG, 13 g/m, on a 0.2 m route
            wire("lead.XT60.-", "reg.J.GND", route="leads"),
            wire("reg.J.VOUT", "servo.pads.V+", awg=26, length_mm=100),  # 2 g/m
            wire("reg.J.GND", "servo.pads.GND", awg=26, length_mm=100),
        ],
    }
    design = ConnectionList.model_validate(data)
    routes = {"leads": ("base", 0.2)}
    wiring = Wiring(design, ALL, LIST, set(routes), 25.2)
    return design, wiring, routes


def test_the_wiring_weighs_its_wires_plugs_and_heat_shrink_by_hand():
    design, wiring, routes = made_up()
    found = mass.wiring_masses(design, ALL, wiring, routes, lead_part="t-lead")
    base, p = found["base"], found["P"]
    assert base.meters == pytest.approx(0.4)
    assert base.wires == pytest.approx(0.4 * 13e-3)
    # the XT60's half once, and the wire's half of each JST position the leads land in (the
    # regulator's VIN and GND; GND has two wires but is one position)
    assert base.plugs == pytest.approx(XT60 / 1000 + 2 * GH / 2 / 1000)
    assert base.sleeving == pytest.approx(0.2 * mass.SLEEVE_G_PER_M / 1000)  # over both leads
    # the servo's wires go to P (an end in a module), and its two soldered ends get heat shrink
    assert p.wires == pytest.approx(0.2 * 2e-3)
    assert p.shrink == pytest.approx(2 * mass.SHRINK_G / 1000)
    # the regulator's VOUT position is on the servo's wire, so its half goes with P
    assert p.plugs == pytest.approx(GH / 2 / 1000) and p.sleeving == 0
    assert base.total == pytest.approx(base.wires + base.plugs + base.shrink + base.sleeving)


@pytest.fixture
def copy(tmp_path):
    shutil.copytree(ROOT / "design" / "catalog", tmp_path / "catalog")
    shutil.copy(ROOT / "design" / "build.yaml", tmp_path / "build.yaml")
    return tmp_path


def _masses():
    return {
        "base": mass.WiringMass("base", 6.5, 0.052, 0.005, 0.0034, 0.0006, 140),
        "V": mass.WiringMass("V", 0.7, 0.002, 0.0, 0.0001, 0.0, 4),
        "P": mass.WiringMass("P", 0.7, 0.0024, 0.0, 0.0006, 0.0, 19),
        "C": mass.WiringMass("C", 0.5, 0.0021, 0.0, 0.0002, 0.0, 6),
    }


def test_the_catalog_takes_the_wiring_and_only_the_wiring(copy):
    before = {p.relative_to(copy): p.read_bytes() for p in (copy / "catalog").rglob("*.yaml")}
    changed = mass.update_catalog(_masses(), copy / "catalog", copy / "build.yaml", 4.2e-3)
    names = {p.name for p in changed}
    assert names == {"base-wiring.yaml", "v-wiring.yaml", "p-wiring.yaml", "c-wiring.yaml",
                     "build.yaml"}  # fmt: skip
    wiring = {"base-wiring.yaml", "v-wiring.yaml", "p-wiring.yaml", "c-wiring.yaml"}
    for path, text in before.items():
        if path.name not in wiring:
            assert (copy / path).read_bytes() == text, path

    from pcs14.catalog import SourceKind, load_catalog
    from pcs14.design import load_build

    catalog = load_catalog(copy / "catalog")
    base = catalog.component("base-wiring")
    assert base.mass == pytest.approx(0.0610)
    assert base.source.kind == SourceKind.ESTIMATE and "connection list" in base.source.note
    assert base.electrical is not None  # the XT60's pins stay
    build = load_build(copy / "build.yaml", catalog)
    assert "v-wiring" in {p.id for p in build.modules["V"]}
    assert build.pack.wiring_resistance == pytest.approx(4.2e-3)
    assert "connection list" in yaml.safe_load((copy / "build.yaml").read_text())["pack"]["note"]


def test_running_it_twice_changes_nothing_more(copy):
    mass.update_catalog(_masses(), copy / "catalog", copy / "build.yaml", 4.2e-3)
    once = {p: p.read_bytes() for p in copy.rglob("*.yaml")}
    mass.update_catalog(_masses(), copy / "catalog", copy / "build.yaml", 4.2e-3)
    assert {p: p.read_bytes() for p in copy.rglob("*.yaml")} == once
