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


@pytest.fixture(scope="module")
def loads(real):
    from pcs14.electrical.loads import solve_all

    catalog, build, design, settings, _ = real
    targets = load_targets(ROOT / "design" / "targets.yaml")
    return solve_all(design, catalog, build, targets, settings)


def test_every_combination_gets_every_flight_case(loads):
    assert len(loads) == 8 * 4
    assert {case for _, case in loads} == {"hover", "cruise", "burst", "worst"}


def test_the_battery_leads_carry_the_sizing_models_current(loads):
    for (setup, case), result in loads.items():
        lead = result.wire_amps("lead.XT60.+ to esc.BAT.VBAT")
        assert lead == pytest.approx(result.case.battery_amps, rel=0.01), (setup, case)
        ground = result.wire_amps("lead.XT60.- to esc.BAT.GND")
        assert ground == pytest.approx(lead, rel=0.02), (setup, case)


def test_the_burst_is_the_current_cap(loads):
    assert loads[("max", "burst")].case.battery_amps == pytest.approx(90.0)


def test_the_module_supply_carries_what_the_talk_worked_out(loads):
    # the talk's table: about 2.5 A typical in Max, 5.6 A with every servo stalled
    assert 2.3 <= loads[("max", "hover")].supply_amps("bec.5V") <= 2.9
    assert 5.4 <= loads[("max", "worst")].supply_amps("bec.5V") <= 6.3


def test_the_safety_monitor_runs_off_the_higher_supply(loads):
    result = loads[("base", "hover")]
    assert result.element_amps("teensy_feed.D_MODULE") > 0.05  # the module supply's 5.2 V
    assert result.element_amps("teensy_feed.D_FC") == pytest.approx(0.0)


def test_the_pi_sees_more_than_5v_on_a_normal_day(loads):
    for (setup, case), result in loads.items():
        if "V" in result.modules and case != "worst":
            assert result.volts("pi.GPIO.5V") > 5.0, (setup, case)
