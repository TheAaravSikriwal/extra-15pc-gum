"""Finding where a pin sits (pcs14.electrical.pins), on made-up parts."""

from datetime import date

from pcs14.catalog.cad import CadConnector
from pcs14.catalog.source import Source
from pcs14.electrical import pins

DRAWING = Source(kind="manufacturer", url="https://example.com/a.pdf", checked=date(2026, 10, 21))


def test_a_connector_lists_each_pin_where_the_drawing_puts_it():
    c = CadConnector(name="ESC", side="top", faces="+x", source=DRAWING,
                     pins={"VBAT": (16.3, -8.9), "GND": (16.3, -0.15)})  # fmt: skip
    assert c.pins["GND"] == (16.3, -0.15)
    assert c.z(thickness_mm=1.6) == 1.6  # on top of the board
    under = CadConnector(name="J1", side="bottom", source=DRAWING, pins={"A": (0, 0)})
    assert under.z(1.6) == 0
    edge = CadConnector(name="J1", side="edge", z_mm=4.9, source=DRAWING, pins={"A": (0, 0)})
    assert edge.z(2) == 4.9  # as it says


def test_a_row_of_pins_from_its_first_one():
    row = pins.row(["VBAT", "CURR", "TLM"], first=(16.3, -8.9), pitch_mm=1.25, runs=(0, 1))
    assert row == {"VBAT": (16.3, -8.9), "CURR": (16.3, -7.65), "TLM": (16.3, -6.4)}
