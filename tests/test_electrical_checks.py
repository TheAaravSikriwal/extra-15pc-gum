"""The electrical checks, each on a small made-up case with a hand-worked answer."""

import math

import pytest

from electrical_parts import LISTED, PARTS, connector, part
from pcs14.electrical import checks
from pcs14.electrical.loads import Case, solve_case
from pcs14.electrical.model import CheckNumbers, ConnectionList
from test_electrical_loads import ALL, ALL_LISTED, buck_and_load, wire

NUMBERS = CheckNumbers(
    continuous_share=0.8,
    burst_s=10,
    air_c=40,
    temp_margin_c=20,
    main_drop_share=0.02,
    load_margin_v=0.1,
    pin_minimums={},
    supply_typical_share=0.8,
    fuse_hold_factor=1.25,
    cell_link_blow_s=1.0,
    rise_share=0.1,
    threshold_margin_share=0.1,
)


def solutions_for(data, cases, parts=ALL, listed=ALL_LISTED):
    design = ConnectionList.model_validate(data)
    out = {}
    for case in cases:
        out[("test", case.name)] = solve_case(design, parts, listed, {}, frozenset(), case, 25.2)
    return design, out


def context(design, parts=ALL, listed=ALL_LISTED, **kw):
    return checks.Context.make(design, parts, listed, NUMBERS, pack_nominal=21.6, **kw)


def failed(findings):
    return [f for f in findings if not f.passed]


HOVER = Case("hover", pack_volts=25.0, draw="typical")
WORST = Case("worst", pack_volts=25.0, draw="worst")


def test_a_supply_at_its_typical_share_passes_and_past_it_fails():
    design, solutions = solutions_for(buck_and_load(), [HOVER, WORST])
    found = checks.supplies(context(design), solutions)
    regulator = [f for f in found if f.subject == "reg.5V"]
    # 1 A typical against 2 A continuous: 50%, under the 80% line
    assert regulator and all(f.passed for f in regulator)
    heavy = part(
        "t-5v-1a8",
        {
            "connectors": [connector("J", "5V power max_volts=5.5", "GND ground")],
            "draws": [{"pin": "J.5V", "min_v": 4, "max_v": 5.5, "typical_a": 1.8, "worst_a": 2.5}],
        },
    )
    parts, listed = {**ALL, "t-5v-1a8": heavy}, {**ALL_LISTED, "t-5v-1a8": {"base"}}
    design, solutions = solutions_for(buck_and_load(load="t-5v-1a8"), [HOVER, WORST], parts, listed)
    found = failed(checks.supplies(context(design, parts, listed), solutions))
    assert {f.where.split(", ")[1] for f in found} == {"hover", "worst"}  # 1.8 > 1.6, 2.5 > 2


def test_a_contact_past_80_percent_of_its_rating_fails():
    # the made-up family carries 1 A a contact; 0.9 A is past 0.8 A
    heavy = part(
        "t-socketed-load",
        {
            "connectors": [connector("J", "IN power max_volts=30", "GND ground")],
            "draws": [{"pin": "J.IN", "min_v": 10, "max_v": 30, "typical_a": 0.9, "worst_a": 0.9}],
        },
    )
    parts, listed = {**ALL, "t-socketed-load": heavy}, {**ALL_LISTED, "t-socketed-load": {"base"}}
    data = {
        "boards": {"load": {"part": "t-socketed-load"}},
        "wires": [wire("pack.XT60.+", "load.J.IN"), wire("pack.XT60.-", "load.J.GND")],
    }
    design, solutions = solutions_for(data, [HOVER], parts, listed)
    found = failed(checks.connector_currents(context(design, parts, listed), solutions))
    assert {f.subject for f in found} == {"load.J.IN", "load.J.GND"}
    assert found[0].value == pytest.approx(0.9) and found[0].limit == pytest.approx(0.8)


def test_a_load_outside_its_range_with_the_margin_fails():
    # the made-up 1 A load takes 4 to 5.5 V: 5 V less a short lead is fine, 60 m of it isn't
    design, solutions = solutions_for(buck_and_load(), [HOVER])
    assert failed(checks.load_voltages(context(design), solutions)) == []
    data = buck_and_load()
    data["wires"][2] = wire("reg.J.VOUT", "load.J.5V", 60000)  # 60 m of 21 mOhm/m at 1 A
    design, solutions = solutions_for(data, [HOVER])
    found = failed(checks.load_voltages(context(design), solutions))
    assert [f.subject for f in found] == ["load.J.5V"]
    assert found[0].value == pytest.approx(5 - 60 * 0.021, abs=0.01)


def test_a_pin_minimum_overrides_the_margin():
    design, solutions = solutions_for(buck_and_load(), [HOVER])
    numbers = NUMBERS.model_copy(update={"pin_minimums": {"load.J.5V": 5.05}})
    ctx = checks.Context.make(design, ALL, ALL_LISTED, numbers, pack_nominal=21.6)
    found = failed(checks.load_voltages(ctx, solutions))
    assert [f.limit for f in found] == [5.05]


def test_a_pin_ceiling_is_checked_without_the_margin():
    # the made-up load takes up to 5.5 V; on a 5.45 V rail the margin's 5.4 V ceiling fails it,
    # and a pin ceiling (for a part whose maker publishes no maximum) checks it at 5.5 V itself
    data = buck_and_load()
    regulator = ALL["t-buck"].model_dump(mode="json")
    regulator["id"] = "t-buck-545"
    regulator["electrical"]["outputs"][0]["volts"] = 5.45
    from pcs14.catalog.schema import Component

    parts = {**ALL, "t-buck-545": Component.model_validate(regulator)}
    listed = {**ALL_LISTED, "t-buck-545": {"base"}}
    data["boards"]["reg"] = {"part": "t-buck-545"}
    design, solutions = solutions_for(data, [HOVER], parts, listed)
    plain = context(design, parts, listed)
    assert [f.subject for f in failed(checks.load_voltages(plain, solutions))] == ["load.J.5V"]
    numbers = NUMBERS.model_copy(update={"pin_ceilings": {"load.J.5V": 5.5}})
    ctx = checks.Context.make(design, parts, listed, numbers, pack_nominal=21.6)
    found = checks.load_voltages(ctx, solutions)
    assert failed(found) == [] and "no margin" in found[0].detail


def esc_drone(lead_mm):
    esc = part(
        "t-esc",
        {
            "connectors": [
                connector("BAT", "VBAT power max_volts=26", "GND ground", family="pads")
            ],
            "draws": [
                {"pin": "BAT.VBAT", "min_v": 12, "max_v": 26, "typical_a": 0.0, "worst_a": 0.0}
            ],
        },
    ).model_copy(update={"type": "esc"})
    parts, listed = {**ALL, "t-esc": esc}, {**ALL_LISTED, "t-esc": {"base"}}
    data = {
        "boards": {"esc": {"part": "t-esc"}},
        "wires": [
            wire("pack.XT60.+", "esc.BAT.VBAT", lead_mm),
            wire("pack.XT60.-", "esc.BAT.GND", lead_mm),
        ],
    }
    burst = Case("burst", pack_volts=20.0, draw="typical", battery_amps=90.0)
    design, solutions = solutions_for(data, [burst], parts, listed)
    return checks.main_drop(context(design, parts, listed), solutions)


def test_the_main_path_drop_at_the_cap():
    # 2% of 21.6 V is 0.432 V; at 90 A that's 4.8 mOhm out and back, 2.4 mOhm each way:
    # 114 mm of the made-up 21 mOhm/m wire
    short, long = esc_drone(100)[0], esc_drone(130)[0]
    assert short.passed and short.value == pytest.approx(90 * 2 * 0.0021, rel=1e-3)
    assert not long.passed
    assert short.limit == pytest.approx(0.432)


def fused(rating):
    data = {
        "boards": {"fuses": {"part": "t-fuses"}, "load": {"part": "t-24v-load"}},
        "wires": [
            wire("pack.XT60.+", "fuses.F.A", 10),
            wire("fuses.F.B", "load.J.IN", 100, awg=26),
            wire("pack.XT60.-", "load.J.GND", 100),
        ],
        "fuses": [{"element": "fuses.F1", "family": "t-fuse-family-wide", "rated_a": rating}],
    }
    family = part(
        "t-fuse-family-wide",
        {
            "fuse": {
                "volts": 32,
                "interrupting_a": 1000,
                "max_c": 125,
                "ratings": [
                    {"rated_a": 2, "cold_mohm": 55, "melting_i2t_a2s": 9},
                    {"rated_a": 3, "cold_mohm": 30, "melting_i2t_a2s": 20},
                    {"rated_a": 40, "cold_mohm": 2, "melting_i2t_a2s": 5000},
                ],
            }
        },
    )
    parts = {**ALL, "t-fuse-family-wide": family}
    design, solutions = solutions_for(data, [HOVER], parts)
    return checks.fuses(context(design, parts), solutions)


def test_a_fuse_holds_125_percent_of_its_steady_current():
    # the made-up load takes 2 A, so a fuse needs 2.5 A: 3 A holds it, 2 A doesn't
    holds = [f for f in fused(3) if f.check == "fuse holds"]
    assert holds and holds[0].passed
    assert not [f for f in fused(2) if f.check == "fuse holds"][0].passed


def test_a_fuse_has_to_blow_before_its_wire_cooks():
    # 26 AWG made-up wire: 0.128 mm2 of copper heated from 40 to 200 C takes this many A2s
    area = 0.1287e-6  # 26 AWG by its definition
    wire_i2t = (
        area**2
        * 8960
        * 385
        / (1.724e-8 * 0.00393)
        * math.log((1 + 0.00393 * 180) / (1 + 0.00393 * 20))
    )
    protects = {f.subject: f for f in fused(3) if f.check == "fuse protects its wire"}
    assert protects["fuses.F1"].passed and protects["fuses.F1"].limit == pytest.approx(
        wire_i2t, rel=0.01
    )
    # a 40 A fuse lets through 5000 A2s, far past what 26 AWG takes
    assert not [f for f in fused(40) if f.check == "fuse protects its wire"][0].passed


def test_onderdonk_by_hand():
    # 18 AWG: 0.823 mm2, 1624 circular mils, from 40 C
    assert checks.onderdonk_seconds(0.823e-6, 45, 40) == pytest.approx(26.9, abs=0.1)
    assert checks.onderdonk_seconds(0.823e-6, 262, 40) == pytest.approx(0.79, abs=0.01)
    assert checks.onderdonk_celsius(0.823e-6, 45, 10, 40) == pytest.approx(257, abs=1)


@pytest.mark.parametrize(
    "awg, area, holds, blows", [(16, 1.31e-6, True, False), (18, 0.823e-6, False, True)]
)
def test_the_cell_links_trade_heat_for_speed(awg, area, holds, blows):
    # 16 AWG stays at 111 C through a 10 s burst at 45 A but takes 2 s to blow at 262 A;
    # 18 AWG blows in 0.79 s but reaches 257 C, past a solder joint's 183 C less 20
    found = checks.cell_links(NUMBERS, awg, area, 45.0, 262.0, 183.0)
    by = {f.check: f for f in found}
    assert by["cell link holds the burst"].passed is holds
    assert by["cell link blows on a short"].passed is blows


def test_awg_areas_by_definition():
    assert checks.awg_area(26) == pytest.approx(0.1287e-6, rel=1e-3)
    assert checks.awg_area(12) == pytest.approx(3.309e-6, rel=1e-3)


def test_a_check_says_when_it_rests_on_an_estimate():
    guessed = part(
        "t-guessed-load",
        {
            "connectors": [connector("J", "5V power max_volts=5.5", "GND ground")],
            "draws": [{"pin": "J.5V", "min_v": 4, "max_v": 5.5, "typical_a": 1, "worst_a": 1}],
            "estimates": ["draws[J.5V]"],
            "estimate_note": "a guess",
        },
    )
    parts, listed = {**ALL, "t-guessed-load": guessed}, {**ALL_LISTED, "t-guessed-load": {"base"}}
    design, solutions = solutions_for(buck_and_load(load="t-guessed-load"), [HOVER], parts, listed)
    found = checks.load_voltages(context(design, parts, listed), solutions)
    assert found[0].rests_on == ("t-guessed-load: draws[J.5V]",)


def test_the_parts_lists_used_by_the_tests_are_untouched():
    assert "t-guessed-load" not in PARTS and "t-guessed-load" not in LISTED
