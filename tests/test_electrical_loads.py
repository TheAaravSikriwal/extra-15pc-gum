"""The current in every wire and the voltage at every pin, on small made-up drones worked out
by hand."""

import pytest

from electrical_parts import LISTED, PARTS, connector, part
from pcs14.electrical.loads import Case, solve_case
from pcs14.electrical.model import ConnectionList

WIRE_R = 0.021  # ohms per meter, the made-up 18 AWG


def wire(a, b, length_mm=1000, awg=18):
    return {"ends": [a, b], "wire": "t-wire", "awg": awg, "length_mm": length_mm, "harness": "h"}


EXTRA = {
    p.id: p
    for p in [
        part(
            "t-24v-load",
            {
                "connectors": [connector("J", "IN power max_volts=30", "GND ground")],
                "draws": [{"pin": "J.IN", "min_v": 10, "max_v": 30, "typical_a": 2, "worst_a": 3}],
            },
        ),
        part(
            "t-5v-1a",
            {
                "connectors": [connector("J", "5V power max_volts=5.5", "GND ground")],
                "draws": [{"pin": "J.5V", "min_v": 4, "max_v": 5.5, "typical_a": 1, "worst_a": 1}],
            },
        ),
        part(
            "t-buck",
            {
                "connectors": [
                    connector("J", "VIN power max_volts=30", "VOUT power volts=5", "GND ground")
                ],
                "draws": [
                    {"pin": "J.VIN", "min_v": 6, "max_v": 30, "typical_a": 0.01, "worst_a": 0.01}
                ],
                "outputs": [
                    {
                        "name": "5V",
                        "fed_from": "J.VIN",
                        "pins": ["J.VOUT"],
                        "volts": 5,
                        "continuous_a": 2,
                        "efficiency": 0.8,
                    }
                ],
            },
        ),
        part(
            "t-buck-5v2",
            {
                "connectors": [
                    connector("J", "VIN power max_volts=30", "VOUT power volts=5.2", "GND ground")
                ],
                "outputs": [
                    {
                        "name": "5V",
                        "fed_from": "J.VIN",
                        "pins": ["J.VOUT"],
                        "volts": 5.2,
                        "continuous_a": 2,
                        "efficiency": 0.8,
                    }
                ],
            },
        ),
        part(
            "t-ldo",
            {
                "connectors": [
                    connector("J", "VIN power max_volts=6", "VOUT power volts=3.3", "GND ground")
                ],
                "outputs": [
                    {
                        "name": "3V3",
                        "kind": "linear",
                        "fed_from": "J.VIN",
                        "pins": ["J.VOUT"],
                        "volts": 3.3,
                        "continuous_a": 0.5,
                        "own_a": 0.1,
                    }
                ],
            },
        ),
        part(
            "t-3v3-load",
            {
                "connectors": [connector("J", "IN power max_volts=3.6", "GND ground")],
                "draws": [
                    {"pin": "J.IN", "min_v": 3, "max_v": 3.6, "typical_a": 0.2, "worst_a": 0.2}
                ],
            },
        ),
    ]
}
ALL = {**PARTS, **EXTRA}
ALL_LISTED = {**LISTED, **{part_id: {"base"} for part_id in EXTRA}}


def solve(data, case=None, modules=frozenset()):
    case = case or Case("hover", pack_volts=25.0, draw="typical")
    return solve_case(ConnectionList.model_validate(data), ALL, ALL_LISTED, {}, modules, case, 25.2)


def test_a_load_on_the_pack_and_its_ground_return():
    data = {
        "boards": {"load": {"part": "t-24v-load"}},
        "wires": [wire("pack.XT60.+", "load.J.IN"), wire("pack.XT60.-", "load.J.GND")],
    }
    result = solve(data)
    assert result.wire_amps("pack.XT60.+ to load.J.IN") == pytest.approx(2.0)
    assert result.wire_amps("pack.XT60.- to load.J.GND") == pytest.approx(2.0)
    # 2 A through 21 mOhm out and 21 mOhm back
    assert result.volts("load.J.IN") == pytest.approx(25.0 - 2 * 2 * WIRE_R)
    worst = solve(data, Case("hover", pack_volts=25.0, draw="worst"))
    assert worst.wire_amps("pack.XT60.+ to load.J.IN") == pytest.approx(3.0)


def buck_and_load(load="t-5v-1a", regulator="t-buck"):
    return {
        "boards": {"reg": {"part": regulator}, "load": {"part": load}},
        "wires": [
            wire("pack.XT60.+", "reg.J.VIN", 10),
            wire("pack.XT60.-", "reg.J.GND", 10),
            wire("reg.J.VOUT", "load.J.5V", 10),
            wire("reg.J.GND", "load.J.GND", 10),
        ],
    }


def test_a_switching_regulator_draws_its_output_power_over_its_efficiency():
    result = solve(buck_and_load())
    assert result.supply_amps("reg.5V") == pytest.approx(1.0)
    v_in = result.volts("reg.J.VIN")
    assert result.wire_amps("pack.XT60.+ to reg.J.VIN") == pytest.approx(
        5 * 1 / (0.8 * v_in) + 0.01, rel=1e-3
    )
    assert result.wire_amps("pack.XT60.+ to reg.J.VIN") == pytest.approx(0.26, abs=0.002)


def test_a_linear_regulator_passes_its_current_straight_through():
    data = buck_and_load()
    data["boards"]["ldo"] = {"part": "t-ldo"}
    data["boards"]["small"] = {"part": "t-3v3-load"}
    data["wires"] += [
        wire("reg.J.VOUT", "ldo.J.VIN", 10),
        wire("reg.J.GND", "ldo.J.GND", 10),
        wire("ldo.J.VOUT", "small.J.IN", 10),
        wire("ldo.J.GND", "small.J.GND", 10),
    ]
    result = solve(data)
    assert result.wire_amps("reg.J.VOUT to ldo.J.VIN") == pytest.approx(0.2 + 0.1)
    assert result.supply_amps("reg.5V") == pytest.approx(1.0 + 0.3)


def test_the_higher_supply_carries_a_diode_or():
    data = {
        "boards": {
            "high": {"part": "t-buck-5v2"},
            "low": {"part": "t-buck"},
            "diodes": {"part": "t-diodes"},
            "load": {"part": "t-5v-1a"},
        },
        "wires": [
            wire("pack.XT60.+", "high.J.VIN", 10),
            wire("pack.XT60.-", "high.J.GND", 10),
            wire("pack.XT60.+", "low.J.VIN", 10),
            wire("pack.XT60.-", "low.J.GND", 10),
            wire("high.J.VOUT", "diodes.D.A1", 1),
            wire("low.J.VOUT", "diodes.D.A2", 1),
            wire("diodes.D.K", "load.J.5V", 1),
            wire("high.J.GND", "load.J.GND", 1),
        ],
    }
    result = solve(data)
    assert result.element_amps("diodes.D1") == pytest.approx(1.0)
    assert result.element_amps("diodes.D2") == pytest.approx(0.0)
    # the made-up diode drops 0.8 V
    assert result.volts("load.J.5V") == pytest.approx(5.2 - 0.8, abs=0.002)


def test_parallel_grounds_split_by_their_resistance():
    data = {
        "boards": {"load": {"part": "t-24v-load"}},
        "wires": [
            wire("pack.XT60.+", "load.J.IN"),
            wire("pack.XT60.-", "load.J.GND", 1000),
            wire("pack.XT60.-", "load.J.GND", 2000) | {"name": "the long ground"},
        ],
    }
    result = solve(data)
    assert result.wire_amps("pack.XT60.- to load.J.GND") == pytest.approx(2 * 2 / 3)
    assert result.wire_amps("the long ground") == pytest.approx(2 * 1 / 3)


def test_a_fuses_cold_resistance_drops_volts():
    data = {
        "boards": {"fuses": {"part": "t-fuses"}, "load": {"part": "t-24v-load"}},
        "wires": [
            wire("pack.XT60.+", "fuses.F.A", 1),
            wire("fuses.F.B", "load.J.IN", 1),
            wire("pack.XT60.-", "load.J.GND", 1),
        ],
        "fuses": [{"element": "fuses.F1", "family": "t-fuse-family", "rated_a": 3}],
    }
    result = solve(data)
    assert result.element_amps("fuses.F1") == pytest.approx(2.0)
    # 30 mOhm cold resistance, and three 1 mm runs of wire
    assert result.volts("load.J.IN") == pytest.approx(25.0 - 2 * 0.030 - 3 * 2 * WIRE_R / 1000)


def test_the_esc_takes_the_sizing_models_battery_current():
    esc = part(
        "t-esc",
        {
            "connectors": [
                connector("BAT", "VBAT power max_volts=26", "GND ground", family="pads"),
                connector("MOTORS", "M1A power", family="pads"),
            ],
            "draws": [
                {"pin": "BAT.VBAT", "min_v": 12, "max_v": 26, "typical_a": 0.05, "worst_a": 0.05}
            ],
        },
    )
    esc = esc.model_copy(update={"type": "esc"})
    motor = part("t-motor", {"connectors": [connector("leads", "A power", family="pads")]})
    motor = motor.model_copy(update={"type": "motor"})
    parts = {**ALL, "t-esc": esc, "t-motor": motor}
    listed = {**ALL_LISTED, "t-esc": {"base"}, "t-motor": {"base"}}
    data = {
        "boards": {
            "esc": {"part": "t-esc"},
            "m1": {"part": "t-motor"},
            "load": {"part": "t-24v-load"},
        },
        "wires": [
            wire("pack.XT60.+", "esc.BAT.VBAT", 100),
            wire("pack.XT60.-", "esc.BAT.GND", 100),
            wire("esc.BAT.VBAT", "load.J.IN", 10),
            wire("esc.BAT.GND", "load.J.GND", 10),
            wire("esc.MOTORS.M1A", "m1.leads.A", 200),
        ],
    }
    case = Case("hover", pack_volts=24.0, draw="typical", battery_amps=20.0, motor_amps=17.0)
    result = solve_case(
        ConnectionList.model_validate(data), parts, listed, {}, frozenset(), case, 25.2
    )
    assert result.wire_amps("pack.XT60.+ to esc.BAT.VBAT") == pytest.approx(20.0)
    assert result.wire_amps("esc.MOTORS.M1A to m1.leads.A") == pytest.approx(17.0)
    assert result.wire_amps("esc.BAT.VBAT to load.J.IN") == pytest.approx(2.0)
