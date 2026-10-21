"""Where every wire lands: each pin a wire in design/electrical.yaml ends on is placed on its
part (the cad block's connectors), with where that came from and estimates marked, so the site
can draw every wire pin to pin."""

from pathlib import Path

import pytest

from pcs14.catalog import load_catalog
from pcs14.catalog.source import SourceKind
from pcs14.electrical import pins
from pcs14.electrical.model import load_connection_list

ROOT = Path(__file__).resolve().parents[1]


@pytest.fixture(scope="module")
def catalog():
    return load_catalog(ROOT / "design" / "catalog")


@pytest.fixture(scope="module")
def connections():
    return load_connection_list(ROOT / "design" / "electrical.yaml")


def placed(catalog):
    for part in catalog.all_parts():
        for connector in part.cad.connectors if part.cad else []:
            yield part, connector


def test_every_pin_a_wire_lands_on_has_a_place(catalog, connections):
    missing = [end for wire in connections.wires for end in wire.ends
               if pins.place(catalog, connections, end) is None]  # fmt: skip
    assert missing == []


def test_a_plug_mated_to_a_placed_connector_sits_where_it_does(catalog, connections):
    # the module bus harness's 4-pin plug is in the flight controller's CAN port
    where = pins.place(catalog, connections, "sockets.FC_CAN.CAN_P")
    assert where.board == "fc" and where.connector.name == "CAN"


def test_each_placed_connector_is_a_real_one_with_its_source(catalog):
    for part, connector in placed(catalog):
        named = {c.name: c for c in part.electrical.connectors}
        assert connector.name in named, (part.id, connector.name)
        assert set(connector.pins) <= {p.name for p in named[connector.name].pins}, part.id
        # a maker's drawing says where; an estimate says how it was worked out
        assert connector.source.url or connector.source.note, (part.id, connector.name)


def test_the_pins_sit_on_their_parts(catalog):
    # a frame turned the wrong way would put pins off the board
    for part, connector in placed(catalog):
        cad = part.cad
        if cad.shape not in ("board", "box"):
            continue
        half_length, half_width = cad.length_mm / 2, cad.width_mm / 2
        for name, (x, y) in connector.pins.items():
            assert abs(x) <= half_length + 0.5 and abs(y) <= half_width + 0.5, (part.id, name)


def test_the_drawings_back_most_boards_and_the_rest_are_estimates(catalog):
    kinds = {(part.id, c.name): c.source.kind for part, c in placed(catalog)}
    assert kinds[("pjrc-teensy-41", "pins")] == SourceKind.MANUFACTURER
    assert kinds[("ark-fpv", "ESC")] == SourceKind.MANUFACTURER
    assert kinds[("cjmcu-5018", "J1")] == SourceKind.ESTIMATE  # a seller's photo, nothing more
    assert kinds[("branch-fuses", "F1")] == SourceKind.ESTIMATE
