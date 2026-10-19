"""The harness diagrams, pin maps and power tree, generated from the real connection list."""

from pathlib import Path

import pytest

from pcs14.electrical import diagrams, tools

ROOT = Path(__file__).resolve().parents[1]


@pytest.fixture(scope="module")
def real():
    from pcs14.cad.assembly import wire_length
    from pcs14.cad.settings import load_settings
    from pcs14.catalog import load_catalog
    from pcs14.design import load_build
    from pcs14.electrical.model import load_connection_list

    catalog = load_catalog(ROOT / "design" / "catalog")
    build = load_build(ROOT / "design" / "build.yaml", catalog)
    design = load_connection_list(ROOT / "design" / "electrical.yaml")
    settings = load_settings(ROOT / "design" / "cad.yaml")
    lengths = {w.name: wire_length(w) for w in settings.wires}
    return diagrams.Sources.make(design, catalog, build, lengths)


def test_every_wire_is_in_exactly_one_harness(real):
    harnesses = diagrams.harnesses(real)
    drawn = [cable for spec in harnesses.values() for cable in spec["cables"].values()]
    assert len(drawn) == len(real.design.wires)
    assert {spec_name for spec_name in harnesses} == {w.harness for w in real.design.wires}


def test_a_harness_names_its_connectors_by_board_and_plug(real):
    spec = diagrams.harnesses(real)["receiver"]
    assert {"fc-RC", "rx-pads", "taps-B1"} <= set(spec["connectors"])
    assert spec["connectors"]["fc-RC"]["pinlabels"] == ["5V", "USART6_RX", "USART6_TX", "GND"]


@pytest.mark.skipif(tools.find("dot") is None, reason="Graphviz isn't installed")
def test_the_harnesses_draw(real, tmp_path):
    written = diagrams.draw_harnesses(real, tmp_path)
    assert len(written) == len({w.harness for w in real.design.wires})
    assert all(path.read_text(encoding="utf-8").lstrip().startswith("<") for path in written)


@pytest.mark.parametrize("board", ["fc", "teensy"])
def test_the_pin_maps_cover_every_wire_end(real, board):
    rows = diagrams.pin_map(real, board)
    used = {row["pin"] for row in rows if row["to"]}
    ends = {
        ref.split(".", 1)[1]
        for w in real.design.wires
        for ref in w.ends
        if ref.startswith(f"{board}.")
    }
    assert ends <= used


def test_the_flight_controllers_pin_map_names_px4s_ports(real):
    rows = {row["pin"]: row for row in diagrams.pin_map(real, "fc")}
    assert "TELEM1" in rows["TELEM.UART7_TX"]["functions"]
    assert "lidar.J1.RXD" in rows["GPS.USART1_TX"]["to"]


def test_the_power_tree_reaches_every_supply_and_load(real):
    text = diagrams.power_tree_markdown(real)
    for name in (
        "pack",
        "bec.5V",
        "fc.5V",
        "teensy.3V3",
        "pi.GPIO.5V",
        "chute.servo.V+",
        "fuses.F1",
    ):
        assert name in text, name
