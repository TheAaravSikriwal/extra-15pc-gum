"""The connection list's own rules, on small made-up lists: each test breaks one rule."""

import copy

import pytest

from pcs14.catalog.schema import Component, Wire
from pcs14.electrical.model import ConnectionList
from pcs14.electrical.validate import validate

MADE_UP = {"kind": "made_up", "note": "test numbers"}
BASE = frozenset()
WITH_P = frozenset({"P"})
COMBINATIONS = [BASE, WITH_P]


def part(part_id, electrical, mass_g=1.0):
    return Component.model_validate(
        {
            "type": "component",
            "id": part_id,
            "maker": "Test",
            "model": part_id,
            "source": MADE_UP,
            "mass_g": mass_g,
            "electrical": {"source": MADE_UP, **electrical},
        }
    )


def pins(*specs):
    out = []
    for spec in specs:
        name, role, *rest = spec.split()
        pin = {"name": name, "role": role}
        for item in rest:
            key, value = item.split("=")
            pin[key] = value if key == "direction" else float(value)
        out.append(pin)
    return out


def connector(name, *specs, family="t-gh"):
    return {"name": name, "family": family, "pins": pins(*specs)}


PARTS = {
    p.id: p
    for p in [
        part("t-gh", {"rating": {"continuous_a": 1.0}}),
        part(
            "t-reg",
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
                    }
                ],
            },
        ),
        part(
            "t-load",
            {
                "connectors": [
                    connector(
                        "J",
                        "5V power volts=5 max_volts=5.5",
                        "GND ground",
                        "TX signal direction=out volts=3.3",
                        "RX signal direction=in volts=3.3 max_volts=3.6",
                    )
                ],
                "draws": [
                    {"pin": "J.5V", "min_v": 4.5, "max_v": 5.5, "typical_a": 0.1, "worst_a": 0.2}
                ],
            },
        ),
        part(
            "t-mcu",
            {
                "connectors": [
                    connector(
                        "J",
                        "VIN power max_volts=5.5",
                        "GND ground",
                        "P1 signal direction=both volts=3.3 max_volts=3.3",
                        "P2 signal direction=both volts=3.3 max_volts=3.3",
                    )
                ],
                "draws": [
                    {"pin": "J.VIN", "min_v": 3.6, "max_v": 5.5, "typical_a": 0.1, "worst_a": 0.1}
                ],
            },
        ),
        part(
            "t-5v-logic",
            {
                "connectors": [
                    connector(
                        "J", "5V power volts=5", "GND ground", "OUT signal direction=out volts=5"
                    )
                ],
                "draws": [
                    {"pin": "J.5V", "min_v": 4.5, "max_v": 5.5, "typical_a": 0.01, "worst_a": 0.01}
                ],
            },
        ),
        part(
            "t-diodes",
            {
                "connectors": [connector("D", "A1 power", "A2 power", "K power", family="pads")],
                "diode": {
                    "reverse_v": 30,
                    "continuous_a": 0.2,
                    "forward": [{"amps": 0.1, "volts": 0.8}],
                },
                "elements": [
                    {"name": "D1", "kind": "diode", "between": ["D.A1", "D.K"]},
                    {"name": "D2", "kind": "diode", "between": ["D.A2", "D.K"]},
                ],
            },
        ),
        part(
            "t-node",
            {
                "connectors": [
                    connector("CAN", "5V power volts=5", "CAN_P bus", "CAN_N bus", "GND ground")
                ],
                "draws": [
                    {
                        "pin": "CAN.5V",
                        "min_v": 4.5,
                        "max_v": 5.5,
                        "typical_a": 0.05,
                        "worst_a": 0.05,
                    }
                ],
            },
        ),
        part(
            "t-bus-end",
            {
                "connectors": [
                    connector("CAN", "5V power volts=5", "CAN_P bus", "CAN_N bus", "GND ground")
                ],
                "elements": [
                    {
                        "name": "R",
                        "kind": "resistor",
                        "between": ["CAN.CAN_P", "CAN.CAN_N"],
                        "ohms": 120,
                    }
                ],
            },
        ),
        part(
            "t-socket",
            {
                "connectors": [
                    connector(
                        "S",
                        "5V power",
                        "GND ground",
                        "CAN_P bus",
                        "CAN_N bus",
                        "SIG signal direction=both volts=3.3",
                    )
                ]
            },
        ),
        part(
            "t-plug",
            {
                "connectors": [
                    connector(
                        "S",
                        "5V power",
                        "GND ground",
                        "CAN_P bus",
                        "CAN_N bus",
                        "SIG signal direction=both volts=3.3",
                    )
                ]
            },
        ),
        part(
            "t-odd-plug",
            {
                "connectors": [
                    connector(
                        "S",
                        "5V power",
                        "GND ground",
                        "CAN_P bus",
                        "CAN_N bus",
                        "DATA signal direction=both volts=3.3",
                    )
                ]
            },
        ),
        part(
            "t-fuses",
            {
                "connectors": [connector("F", "A power", "B power", family="pads")],
                "elements": [{"name": "F1", "kind": "fuse", "between": ["F.A", "F.B"]}],
            },
        ),
        part(
            "t-fuse-family",
            {
                "fuse": {
                    "volts": 32,
                    "interrupting_a": 1000,
                    "max_c": 125,
                    "ratings": [{"rated_a": 3, "cold_mohm": 30, "melting_i2t_a2s": 20}],
                }
            },
        ),
        Wire.model_validate(
            {
                "type": "wire",
                "id": "t-wire",
                "maker": "Test",
                "model": "wire",
                "source": MADE_UP,
                "insulation_max_c": 200,
                "gauges": [
                    {
                        "awg": 18,
                        "resistance_mohm_per_m": 21,
                        "outer_diameter_mm": 2.7,
                        "mass_g_per_m": 13,
                    },
                    {
                        "awg": 26,
                        "resistance_mohm_per_m": 135,
                        "outer_diameter_mm": 1.0,
                        "mass_g_per_m": 2,
                    },
                ],
            }
        ),
    ]
}
LISTED = {
    "t-reg": {"base"},
    "t-load": {"base"},
    "t-mcu": {"base"},
    "t-5v-logic": {"base"},
    "t-diodes": {"base"},
    "t-node": {"P"},
    "t-bus-end": {"base"},
    "t-socket": {"base"},
    "t-plug": {"P"},
    "t-odd-plug": {"P"},
    "t-fuses": {"base"},
}
ROUTES = {"main", "signal"}


def power(a, b, route="main"):
    return {"ends": [a, b], "wire": "t-wire", "awg": 18, "route": route, "harness": "power"}


def signal(a, b, length_mm=50):
    return {
        "ends": [a, b],
        "wire": "t-wire",
        "awg": 26,
        "length_mm": length_mm,
        "harness": "signal",
    }


def good():
    return {
        "boards": {
            "reg": {"part": "t-reg"},
            "load": {"part": "t-load"},
            "mcu": {"part": "t-mcu", "modes": {"J.P1": "in"}},
        },
        "wires": [
            power("pack.XT60.+", "reg.J.VIN"),
            power("pack.XT60.-", "reg.J.GND"),
            power("reg.J.VOUT", "load.J.5V"),
            power("reg.J.GND", "load.J.GND"),
            power("reg.J.VOUT", "mcu.J.VIN"),
            power("reg.J.GND", "mcu.J.GND"),
            signal("load.J.TX", "mcu.J.P1"),
        ],
    }


def problems(data, combinations=COMBINATIONS):
    return validate(ConnectionList.model_validate(data), PARTS, LISTED, ROUTES, combinations, 25.2)


def messages(data, **kw):
    return " | ".join(p.message for p in problems(data, **kw))


def test_a_good_list_passes():
    assert problems(good()) == []


def test_a_wire_to_a_pin_that_isnt_there_fails():
    data = good()
    data["wires"].append(signal("load.J.TXD", "mcu.J.P2"))
    assert "load.J.TXD" in messages(data)


def test_two_drivers_on_one_line_fail():
    data = good()
    data["boards"]["mcu"]["modes"] = {"J.P1": "out"}
    assert "two drivers" in messages(data)


def test_two_supplies_tied_together_fail():
    data = good()
    data["boards"]["reg2"] = {"part": "t-reg"}
    data["wires"] += [power("pack.XT60.+", "reg2.J.VIN"), power("pack.XT60.-", "reg2.J.GND")]
    data["wires"].append(power("reg2.J.VOUT", "load.J.5V"))
    assert "two supplies" in messages(data)


def test_two_supplies_through_diodes_pass():
    data = good()
    data["boards"]["reg2"] = {"part": "t-reg"}
    data["boards"]["diodes"] = {"part": "t-diodes"}
    data["wires"] = [w for w in data["wires"] if w["ends"] != ["reg.J.VOUT", "load.J.5V"]]
    data["wires"] += [
        power("pack.XT60.+", "reg2.J.VIN"),
        power("pack.XT60.-", "reg2.J.GND"),
        power("reg.J.VOUT", "diodes.D.A1"),
        power("reg2.J.VOUT", "diodes.D.A2"),
        power("diodes.D.K", "load.J.5V"),
    ]
    assert problems(data) == []


def test_5v_into_a_3v3_pin_fails():
    data = good()
    data["boards"]["logic"] = {"part": "t-5v-logic"}
    data["wires"] += [
        power("reg.J.VOUT", "logic.J.5V"),
        power("reg.J.GND", "logic.J.GND"),
        signal("logic.J.OUT", "mcu.J.P2"),
    ]
    assert "5 V" in messages(data) and "mcu.J.P2" in messages(data)


def test_a_wire_with_no_route_or_length_fails():
    data = good()
    data["wires"].append(
        {"ends": ["load.J.RX", "mcu.J.P2"], "wire": "t-wire", "awg": 26, "harness": "signal"}
    )
    assert "route" in messages(data)


def test_a_route_that_isnt_in_the_cad_fails():
    data = good()
    data["wires"][0]["route"] = "nowhere"
    assert "nowhere" in messages(data)


def test_a_gauge_that_isnt_in_the_wire_table_fails():
    data = good()
    data["wires"][0]["awg"] = 12
    assert "12 AWG" in messages(data)


def test_an_unpowered_board_fails():
    data = good()
    data["wires"] = [w for w in data["wires"] if w["ends"] != ["reg.J.VOUT", "mcu.J.VIN"]]
    assert "mcu.J.VIN isn't powered" in messages(data)


def test_an_ungrounded_board_fails():
    data = good()
    data["wires"] = [w for w in data["wires"] if w["ends"] != ["reg.J.GND", "load.J.GND"]]
    assert "load isn't grounded" in messages(data)


def can_bus(node_terminator):
    data = good()
    data["boards"]["socket"] = {"part": "t-socket"}
    data["boards"]["end"] = {"part": "t-bus-end"}
    data["boards"]["node"] = {"part": "t-node", "terminator": node_terminator}
    data["boards"]["plug"] = {"part": "t-plug"}
    data["mates"] = [{"a": "socket.S", "b": "plug.S"}]
    data["wires"] += [
        power("reg.J.VOUT", "end.CAN.5V"),
        power("reg.J.GND", "end.CAN.GND"),
        power("reg.J.VOUT", "socket.S.5V"),
        power("reg.J.GND", "socket.S.GND"),
        power("plug.S.5V", "node.CAN.5V"),
        power("plug.S.GND", "node.CAN.GND"),
        signal("end.CAN.CAN_P", "socket.S.CAN_P"),
        signal("end.CAN.CAN_N", "socket.S.CAN_N"),
        signal("plug.S.CAN_P", "node.CAN.CAN_P"),
        signal("plug.S.CAN_N", "node.CAN.CAN_N"),
    ]
    return data


def test_a_can_bus_needs_two_terminators_in_every_combination():
    # one fixed terminator in base and one switched on in a module: base alone has just one
    data = can_bus(node_terminator=True)
    found = [p for p in problems(data) if "terminator" in p.message]
    assert found and all(p.combination == BASE for p in found)


def test_a_wire_straight_from_base_into_a_module_fails():
    data = can_bus(node_terminator=False)
    data["wires"].append(signal("mcu.J.P2", "node.CAN.CAN_P"))
    assert "connector" in messages(data)


def test_mated_connectors_need_the_same_pins():
    data = can_bus(node_terminator=False)
    data["boards"]["plug"] = {"part": "t-odd-plug"}
    assert "SIG" in messages(data)


def fused():
    data = good()
    data["boards"]["fuses"] = {"part": "t-fuses"}
    data["wires"][0] = power("pack.XT60.+", "fuses.F.A")
    data["wires"].append(power("fuses.F.B", "reg.J.VIN"))
    return data


def test_a_fuse_needs_a_rating():
    assert "F1" in messages(fused())


def test_a_fuse_with_a_rating_passes_and_carries_power():
    data = fused()
    data["fuses"] = [{"element": "fuses.F1", "family": "t-fuse-family", "rated_a": 3}]
    assert problems(data) == []


def test_a_rating_the_family_doesnt_have_fails():
    data = fused()
    data["fuses"] = [{"element": "fuses.F1", "family": "t-fuse-family", "rated_a": 4}]
    assert "4 A" in messages(data)


def test_a_switch_is_checked_in_both_positions():
    switch = part(
        "t-switch",
        {
            "connectors": [
                connector(
                    "J",
                    "VCC power volts=3.3",
                    "GND ground",
                    "IN signal direction=in volts=3.3",
                    "CM signal direction=both volts=3.3",
                    "NC signal direction=both volts=3.3",
                    "NO signal direction=both volts=3.3",
                )
            ],
            "draws": [{"pin": "J.VCC", "min_v": 1.8, "max_v": 3.6, "typical_a": 0, "worst_a": 0}],
            "switches": [{"control": "J.IN", "common": "J.CM", "low": "J.NC", "high": "J.NO"}],
        },
    )
    parts = {**PARTS, "t-switch": switch}
    listed = {**LISTED, "t-switch": {"base"}}
    data = copy.deepcopy(good())
    data["boards"]["sw"] = {"part": "t-switch"}
    data["boards"]["logic"] = {"part": "t-5v-logic"}
    data["wires"] += [
        power("reg.J.VOUT", "logic.J.5V"),
        power("reg.J.GND", "logic.J.GND"),
        power("reg.J.VOUT", "sw.J.VCC"),
        power("reg.J.GND", "sw.J.GND"),
        signal("mcu.J.P2", "sw.J.CM"),
        signal("logic.J.OUT", "sw.J.NO"),  # only reaches the 3.3 V pin with the switch high
    ]
    found = validate(ConnectionList.model_validate(data), parts, listed, ROUTES, COMBINATIONS, 25.2)
    level = [p for p in found if "mcu.J.P2" in p.message]
    assert level and all("high" in p.message for p in level)


@pytest.mark.parametrize("module, expected", [(None, True), ("P", False)])
def test_a_board_has_to_be_where_the_build_lists_it(module, expected):
    data = good()
    if module:
        data["boards"]["load"]["module"] = module
    assert (problems(data) == []) is expected


def test_pins_joined_on_a_board_share_a_net():
    # a regulator whose input pin also comes out on a second connector, one rail on the board
    twin = part(
        "t-twin-reg",
        {
            "connectors": [
                connector("J", "VIN power max_volts=30", "VOUT power volts=5", "GND ground"),
                connector("AUX", "VIN power max_volts=30"),
            ],
            "joined": [["J.VIN", "AUX.VIN"]],
            "outputs": [
                {
                    "name": "5V",
                    "fed_from": "J.VIN",
                    "pins": ["J.VOUT"],
                    "volts": 5,
                    "continuous_a": 2,
                }
            ],
        },
    )
    data = good()
    data["boards"]["reg"] = {"part": "t-twin-reg"}
    data["wires"][0] = power("pack.XT60.+", "reg.AUX.VIN")  # fed through the second pin
    found = validate(
        ConnectionList.model_validate(data),
        {**PARTS, "t-twin-reg": twin},
        {**LISTED, "t-twin-reg": {"base"}},
        ROUTES,
        COMBINATIONS,
        25.2,
    )
    assert found == []


def test_a_fused_feed_still_carries_the_packs_volts():
    low = part(
        "t-5v-only",
        {
            "connectors": [connector("J", "IN power max_volts=6", "GND ground")],
            "draws": [{"pin": "J.IN", "min_v": 4, "max_v": 6, "typical_a": 0.1, "worst_a": 0.1}],
        },
    )
    data = fused()
    data["fuses"] = [{"element": "fuses.F1", "family": "t-fuse-family", "rated_a": 3}]
    data["boards"]["low"] = {"part": "t-5v-only"}
    data["wires"] += [power("fuses.F.B", "low.J.IN"), power("reg.J.GND", "low.J.GND")]
    found = validate(
        ConnectionList.model_validate(data),
        {**PARTS, "t-5v-only": low},
        {**LISTED, "t-5v-only": {"base"}},
        ROUTES,
        COMBINATIONS,
        25.2,
    )
    assert any("low.J.IN" in p.message and "25.2 V" in p.message for p in found)


def test_an_unused_can_port_isnt_a_bus_of_its_own():
    # the node's spare CAN plug is joined to its first one on the board
    spare = part(
        "t-node-2",
        {
            "connectors": [
                connector("CAN1", "5V power volts=5", "CAN_P bus", "CAN_N bus", "GND ground"),
                connector("CAN2", "5V power volts=5", "CAN_P bus", "CAN_N bus", "GND ground"),
            ],
            "joined": [["CAN1.CAN_P", "CAN2.CAN_P"], ["CAN1.CAN_N", "CAN2.CAN_N"]],
            "draws": [
                {"pin": "CAN1.5V", "min_v": 4.5, "max_v": 5.5, "typical_a": 0.05, "worst_a": 0.05}
            ],
        },
    )
    data = can_bus(node_terminator=False)
    data["boards"]["node"] = {"part": "t-node-2", "terminator": True}
    for run in data["wires"]:
        run["ends"] = [e.replace("node.CAN.", "node.CAN1.") for e in run["ends"]]
    found = validate(
        ConnectionList.model_validate(data),
        {**PARTS, "t-node-2": spare},
        {**LISTED, "t-node-2": {"P"}},
        ROUTES,
        [WITH_P],
        25.2,
    )
    assert [p for p in found if "terminator" in p.message] == []


def test_one_supply_on_several_pins_is_still_one_supply():
    wide = part(
        "t-wide-reg",
        {
            "connectors": [
                connector("J", "VIN power max_volts=30", "VOUT power volts=5", "GND ground"),
                connector("AUX", "VOUT power volts=5"),
            ],
            "outputs": [
                {
                    "name": "5V",
                    "fed_from": "J.VIN",
                    "pins": ["J.VOUT", "AUX.VOUT"],
                    "volts": 5,
                    "continuous_a": 2,
                }
            ],
        },
    )
    data = good()
    data["boards"]["reg"] = {"part": "t-wide-reg"}
    data["wires"].append(power("reg.AUX.VOUT", "load.J.5V"))
    found = validate(
        ConnectionList.model_validate(data),
        {**PARTS, "t-wide-reg": wide},
        {**LISTED, "t-wide-reg": {"base"}},
        ROUTES,
        COMBINATIONS,
        25.2,
    )
    assert found == []


def test_a_required_path_that_isnt_there_fails():
    data = good()
    data["requires"] = [{"name": "the load talks to the mcu", "pins": ["load.J.TX", "mcu.J.P1"]}]
    assert problems(data) == []
    data["wires"] = [w for w in data["wires"] if w["ends"] != ["load.J.TX", "mcu.J.P1"]]
    assert "the load talks to the mcu" in messages(data)


def test_a_required_path_only_counts_when_its_boards_are_fitted():
    data = can_bus(node_terminator=True)
    data["boards"]["end"] = {"part": "t-bus-end"}
    data["requires"] = [
        {"name": "the node is on the bus", "pins": ["node.CAN.CAN_P", "end.CAN.CAN_P"]}
    ]
    found = [p for p in problems(data) if "the node is on the bus" in p.message]
    assert found == []  # wired, and with P out there's nothing to ask of it
