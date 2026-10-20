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


def test_the_burst_is_the_current_cap_or_what_the_pack_gives(loads):
    # the cap is 90 A; at the reserve the pack's own sag (its insides included) holds it to
    # just under that flat out
    assert 89.0 <= loads[("max", "burst")].case.battery_amps <= 90.0


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


def test_the_real_drones_open_findings(real, loads):
    """What the checks find on the real drone right now. When one gets fixed (or a new one
    turns up), this changes on purpose."""
    from pcs14.electrical.checks import check_design

    catalog, build, design, settings, _ = real
    targets = load_targets(ROOT / "design" / "targets.yaml")
    findings = check_design(design, catalog, build, targets, settings, loads)
    failing = sorted({(f.check, f.subject) for f in findings if not f.passed})
    # the release servo's two went with the Schottkys (2026-10-19): through the ideal diodes it
    # gets 5.16 V, and 4.92 V on its backup. The Pi's 5.185 V is checked against USB's 5.25 V
    # without the margin, since Raspberry Pi publishes no maximum
    # and the XT60's went with the firmware's heat limit on the current cap
    assert failing == []
    assert len(findings) > 250
    heat = {f.check for f in findings}
    assert {"wire current", "wire temperature", "wire burst", "connector temperature"} <= heat
    assert {"ESC current", "ESC burst", "motor current"} <= heat


def test_the_firmware_heat_limit_keeps_the_xt60_at_its_limit(real, loads):
    # my firmware eases the 90 A cap as the XT60 nears its limit (decided 2026-10-19), so the
    # burst works it to exactly its limit, and nothing else passes one
    from pcs14.electrical import checks, thermal

    catalog, build, design, settings, _ = real
    assert "pack.XT60" in design.checks.heat_limited
    ctx = checks.design_context(design, catalog, build, settings)
    connectors = thermal.connector_working(ctx, loads)
    assert connectors[("max", "hover")]["pack.XT60.+"] < 1
    assert connectors[("max", "burst")]["pack.XT60.+"] == pytest.approx(1.0)
    assert max(s for shares in connectors.values() for s in shares.values()) <= 1 + 1e-9
    wires = thermal.wire_working(ctx, loads)
    assert max(max(shares.values()) for shares in wires.values()) < 1
    burst = [
        f
        for f in thermal.connector_heat(ctx, loads)
        if f.check == "connector burst" and f.subject == "pack.XT60.+"
    ]
    assert burst and burst[0].passed and "firmware" in burst[0].detail
    curves = {name: curve for name, curve, _ in thermal.burst_curves(ctx, loads)}
    assert max(c for _, c in curves["pack.XT60.+"]) == pytest.approx(100.0)
    # every combination ends at the limit, so the curve shown is the one that gets there soonest:
    # the heaviest hover's, starting hottest
    hottest_start = max(
        thermal._connector_model(ctx, "pack.XT60.+")[0].steady_rise(
            loads[(name, "hover")].contacts["pack.XT60.+"]
        )
        for name, _ in loads
    )
    assert curves["pack.XT60.+"][0][1] == pytest.approx(design.checks.air_c + hottest_start)


def test_the_cases_start_at_the_packs_own_terminals(real, loads):
    # the sizing model's voltage is after the wiring; the solve adds the wiring itself, so the
    # cases hand it the voltage before, or the leads' drop would count twice
    from pcs14.sizing.battery import Pack

    _, build, _, _, _ = real
    targets = load_targets(ROOT / "design" / "targets.yaml")
    pack = Pack(build.pack)
    burst = loads[("max", "burst")].case
    reserve = pack.soc_at_reserve(targets.reserve_fraction)
    cells_only = pack.resistance - build.pack.wiring_resistance
    expected = pack.ocv(reserve) - burst.battery_amps * cells_only
    assert burst.pack_volts == pytest.approx(expected, rel=1e-6)


def test_the_main_paths_resistance_is_its_drop_over_its_current(real, loads):
    from pcs14.electrical import checks

    catalog, build, design, settings, _ = real
    ctx = checks.design_context(design, catalog, build, settings)
    ohms = checks.main_path_ohms(ctx, loads)
    drop = checks.main_drop(ctx, loads)[0]
    assert ohms == pytest.approx(drop.value / 90.0, rel=0.01)  # every burst sits at the cap
    assert 2e-3 < ohms < 6e-3  # 12 AWG leads and an XT60, out and back
