"""The build package's wiring guide, on the real connection list: every wire once, under its
harness, with its cut length."""

import math
from pathlib import Path

from pcs14.cad.assembly import wire_length
from pcs14.cad.settings import load_settings
from pcs14.catalog import load_catalog
from pcs14.electrical.model import load_connection_list
from pcs14.package import wiring

ROOT = Path(__file__).parent.parent


def real_rows():
    design = load_connection_list(ROOT / "design" / "electrical.yaml")
    settings = load_settings(ROOT / "design" / "cad.yaml")
    parts = {p.id: p for p in load_catalog(ROOT / "design" / "catalog").all_parts()}
    routes = {w.name: (w.module, wire_length(w)) for w in settings.wires}
    return design, wiring.rows(design, routes, parts)


def test_every_wire_is_in_the_guide_once_under_its_harness():
    design, rows = real_rows()
    assert len(rows) == len(design.wires)
    text = wiring.render(rows, "2026-10-21")
    for harness in {w.harness for w in design.wires}:
        assert f"## {harness.capitalize()}" in text
    assert sum(line.startswith("| `") for line in text.splitlines()) == len(design.wires)


def test_a_wire_is_cut_to_its_route_or_its_own_length():
    design, rows = real_rows()
    for run, row in zip(design.wires, rows, strict=True):
        assert row.cut_mm > 0
        if run.route is None:
            assert row.cut_mm == run.length_mm
    motors = [r for r in rows if r.harness == "motors"]
    assert motors and all(r.own_lead for r in motors)


def test_a_routed_wire_is_cut_to_its_whole_run_plug_to_plug():
    from pcs14.site.wires3d import wires3d

    design = load_connection_list(ROOT / "design" / "electrical.yaml")
    settings = load_settings(ROOT / "design" / "cad.yaml")
    parts = {p.id: p for p in load_catalog(ROOT / "design" / "catalog").all_parts()}
    routes = {w.name: (w.module, wire_length(w)) for w in settings.wires}
    drawn = {w.label: w for w in wires3d(ROOT / "design").wires}
    runs = {label: w.length_mm / 1000 for label, w in drawn.items()}
    rows = wiring.rows(design, routes, parts, runs=runs)
    for run, row in zip(design.wires, rows, strict=True):
        if run.route is not None:
            assert row.cut_mm == runs[run.label] * 1000
            # never shorter than a straight line between its two pins
            a, b = (e.at_mm for e in drawn[run.label].ends)
            assert row.cut_mm >= math.dist(a, b) - 0.1
