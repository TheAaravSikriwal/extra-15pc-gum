"""The real connection list: it passes every rule in every module combination, and everything in
the build that carries current is on it."""

from pathlib import Path

import pytest

from pcs14.catalog import load_catalog
from pcs14.design import load_build, load_targets
from pcs14.electrical.model import load_connection_list
from pcs14.electrical.validate import listed_in, validate_design

ROOT = Path(__file__).resolve().parents[1]


@pytest.fixture(scope="module")
def real():
    from pcs14.cad.settings import load_settings

    catalog = load_catalog(ROOT / "design" / "catalog")
    build = load_build(ROOT / "design" / "build.yaml", catalog)
    design = load_connection_list(ROOT / "design" / "electrical.yaml")
    combos = [s.modules for s in load_targets(ROOT / "design" / "targets.yaml").combinations()]
    settings = load_settings(ROOT / "design" / "cad.yaml")
    return catalog, build, design, settings, combos


def test_the_real_list_passes_every_rule(real):
    catalog, build, design, settings, combos = real
    problems = validate_design(design, catalog, build, settings, combos)
    assert [str(p) for p in problems] == []


def test_everything_that_carries_current_is_on_the_list(real):
    catalog, build, design, _, _ = real
    on_list = {}
    for board in design.boards.values():
        on_list.setdefault(board.part, []).append(board)
    for part_id, places in listed_in(build).items():
        part = next(p for p in catalog.all_parts() if p.id == part_id)
        if part.electrical is None:
            continue
        assert part_id in on_list, part_id
        if len(places) > 1:
            assert {b.module for b in on_list[part_id]} == places, part_id


def test_the_motors_are_wired_in_px4_order(real):
    _, _, design, _, _ = real
    routes = {
        run.ends[1].split(".")[0]: run.route for run in design.wires if run.harness == "motors"
    }
    assert routes == {
        "m1": "motor leads front right",
        "m2": "motor leads back left",
        "m3": "motor leads front left",
        "m4": "motor leads back right",
    }


def test_losing_a_wire_on_a_safety_path_is_caught(real):
    from pcs14.electrical.model import ConnectionList

    catalog, build, design, settings, combos = real
    data = design.model_dump()
    data["wires"] = [
        w for w in data["wires"] if list(w["ends"]) != ["pplug.SIGNAL.TAKEOVER", "p_switch.U1.S"]
    ]
    problems = validate_design(
        ConnectionList.model_validate(data), catalog, build, settings, combos
    )
    assert any("take over the chute" in p.message for p in problems)
    assert all(p.combination is None or "P" in p.combination for p in problems)
