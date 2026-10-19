"""Made-up parts and a small made-up drone for the electrical layer's tests."""

from pcs14.catalog.schema import Component, Wire

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
