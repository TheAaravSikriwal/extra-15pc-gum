"""Wire routes: each CAD route's thickness comes from the wires the connection list runs through
it, and every long wire has a route of its own."""

import math
from pathlib import Path

import pytest

from pcs14.electrical import routes

ROOT = Path(__file__).resolve().parents[1]


def test_a_bundle_by_hand():
    # two 12 AWG silicone leads, 3.95 mm each: 1.15 times the root of the summed squares
    assert routes.bundle_diameter([3.95, 3.95]) == pytest.approx(1.15 * math.sqrt(2 * 3.95**2))
    # one wire is just its own diameter, and a bundle is never thinner than its thickest wire
    assert routes.bundle_diameter([2.7]) == pytest.approx(2.7)
    assert routes.bundle_diameter([3.95, 0.2]) >= 3.95


def test_updating_the_cad_changes_only_the_thicknesses(tmp_path):
    cad = tmp_path / "cad.yaml"
    cad.write_text(
        "checks: {}\n"
        "wires:\n"
        "  - name: battery leads\n"
        "    diameter_mm: 8 # a guess\n"
        "    path_mm: [[0, 0, 0], [1, 0, 0]]\n"
        "  - name: camera cable\n"
        "    module: V\n"
        "    diameter_mm: 3\n"
        "    path_mm: [[0, 0, 0], [1, 0, 0]]\n",
        encoding="utf-8",
    )
    changed = routes.update_cad_routes(cad, {"battery leads": 6.42})
    text = cad.read_text(encoding="utf-8")
    assert changed == ["battery leads"]
    assert "    diameter_mm: 6.4 # from the electrical connection list\n" in text
    assert "    diameter_mm: 3\n" in text  # routes the list doesn't use stay as they were
    assert routes.update_cad_routes(cad, {"battery leads": 6.42}) == []  # nothing left to change


def test_every_long_wire_has_a_route():
    from pcs14.electrical.model import load_connection_list

    design = load_connection_list(ROOT / "design" / "electrical.yaml")
    unrouted = [w.label for w in design.wires if w.route is None and w.length_mm > routes.JUMPER_MM]
    assert unrouted == []


def test_the_real_routes_are_as_thick_as_their_wires():
    from pcs14.cad.settings import load_settings
    from pcs14.catalog import load_catalog
    from pcs14.electrical.model import load_connection_list

    catalog = load_catalog(ROOT / "design" / "catalog")
    parts = {p.id: p for p in catalog.all_parts()}
    design = load_connection_list(ROOT / "design" / "electrical.yaml")
    wanted = routes.route_diameters(design, parts)
    settings = load_settings(ROOT / "design" / "cad.yaml")
    for wire in settings.wires:
        if wire.name in wanted:
            assert wire.diameter_mm == pytest.approx(wanted[wire.name], abs=0.05), wire.name
