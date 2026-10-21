"""Finding where a pin sits (pcs14.electrical.pins), on made-up parts."""

from datetime import date

import pytest

from pcs14.catalog.cad import CadConnector
from pcs14.catalog.source import Source
from pcs14.electrical import pins

DRAWING = Source(kind="manufacturer", url="https://example.com/a.pdf", checked=date(2026, 10, 21))


def test_a_connector_lists_each_pin_where_the_drawing_puts_it():
    c = CadConnector(name="ESC", side="top", faces="+x", source=DRAWING,
                     pins={"VBAT": (16.3, -8.9), "GND": (16.3, -0.15)})  # fmt: skip
    assert c.pins["GND"] == (16.3, -0.15)


def test_an_edge_connector_says_how_high_it_is():
    with pytest.raises(ValueError, match="needs its z_mm"):
        CadConnector(name="J1", side="edge", source=DRAWING, pins={"A": (0, 0)})


def test_a_row_of_pins_from_its_first_one():
    row = pins.row(["VBAT", "CURR", "TLM"], first=(16.3, -8.9), pitch_mm=1.25, runs=(0, 1))
    assert row == {"VBAT": (16.3, -8.9), "CURR": (16.3, -7.65), "TLM": (16.3, -6.4)}
