"""The catalog's electrical block: pins, draws, supplies and ratings, each with a source, and the
wire table. Made-up parts only; the real parts' blocks get checked in test_catalog_real_electrical.
"""

import pytest
import yaml
from pydantic import ValidationError

from pcs14.catalog import CatalogError, load_catalog
from pcs14.catalog.electrical import ElectricalBlock
from pcs14.catalog.schema import Component, Wire

MADE_UP = {"kind": "made_up", "note": "test numbers"}


def board(**changes):
    block = {
        "source": MADE_UP,
        "connectors": [
            {
                "name": "ESC",
                "family": "test-gh",
                "pins": [
                    {"name": "VBAT", "role": "power", "volts": 25.2},
                    {"name": "CH1", "role": "signal", "direction": "out", "volts": 3.3},
                    {"name": "GND", "role": "ground"},
                ],
            },
            {
                "name": "CAN",
                "family": "test-gh",
                "pins": [
                    {"name": "5V", "role": "power", "volts": 5.0},
                    {"name": "H", "role": "bus"},
                    {"name": "L", "role": "bus"},
                    {"name": "GND", "role": "ground"},
                ],
            },
        ],
        "draws": [{"pin": "ESC.VBAT", "min_v": 5.5, "max_v": 54, "typical_a": 0.1, "worst_a": 0.2}],
        "outputs": [
            {
                "name": "5V",
                "fed_from": "ESC.VBAT",
                "pins": ["CAN.5V"],
                "volts": 5.0,
                "continuous_a": 2.0,
                "own_a": 0.5,
                "efficiency": 0.9,
            }
        ],
    }
    block.update(changes)
    return block


def test_a_board_loads_and_finds_its_pins():
    block = ElectricalBlock.model_validate(board())
    assert block.pin("ESC.CH1").direction == "out"
    assert [ref for ref, _ in block.pins()][:3] == ["ESC.VBAT", "ESC.CH1", "ESC.GND"]
    assert block.output("5V").available == pytest.approx(1.5)  # 2 A, less what the board uses


def test_signal_pins_need_a_direction_and_a_level():
    bad = board()
    bad["connectors"][0]["pins"][1] = {"name": "CH1", "role": "signal"}
    with pytest.raises(ValidationError, match="direction and volts"):
        ElectricalBlock.model_validate(bad)


def test_pin_names_are_unique_on_a_connector():
    bad = board()
    bad["connectors"][0]["pins"].append({"name": "GND", "role": "ground"})
    with pytest.raises(ValidationError, match="GND.*twice"):
        ElectricalBlock.model_validate(bad)


def test_a_draw_on_a_pin_that_isnt_there_fails():
    bad = board(draws=[{"pin": "ESC.VBATT", "min_v": 5, "max_v": 6, "typical_a": 0, "worst_a": 0}])
    with pytest.raises(ValidationError, match="ESC.VBATT isn't a pin"):
        ElectricalBlock.model_validate(bad)


def test_an_output_on_a_pin_that_isnt_there_fails():
    bad = board()
    bad["outputs"][0]["pins"] = ["GPS.5V"]
    with pytest.raises(ValidationError, match="GPS.5V isn't a pin"):
        ElectricalBlock.model_validate(bad)


@pytest.mark.parametrize(
    "draw, message",
    [
        ({"min_v": 6, "max_v": 5, "typical_a": 0.1, "worst_a": 0.2}, "min_v"),
        ({"min_v": 5, "max_v": 6, "typical_a": 0.3, "worst_a": 0.2}, "worst_a"),
    ],
)
def test_draws_make_sense(draw, message):
    bad = board(draws=[{"pin": "ESC.VBAT", **draw}])
    with pytest.raises(ValidationError, match=message):
        ElectricalBlock.model_validate(bad)


@pytest.mark.parametrize(
    "path",
    ["connectors[ESC]", "draws[ESC.VBAT].worst_a", "outputs[5V].continuous_a", "outputs[5V]"],
)
def test_estimates_can_name_anything_real(path):
    block = ElectricalBlock.model_validate(board(estimates=[path], estimate_note="a guess"))
    assert block.estimates == [path]


@pytest.mark.parametrize(
    "path", ["connectors[GPS]", "draws[ESC.VBAT].peak_a", "outputs[12V]", "rating.continuous_a"]
)
def test_estimates_naming_something_that_isnt_there_fail(path):
    with pytest.raises(ValidationError, match="estimates"):
        ElectricalBlock.model_validate(board(estimates=[path], estimate_note="a guess"))


def test_estimates_need_a_note():
    with pytest.raises(ValidationError, match="estimate_note"):
        ElectricalBlock.model_validate(board(estimates=["connectors[ESC]"]))


def fuse_block(ratings):
    return {
        "source": MADE_UP,
        "fuse": {"volts": 32, "interrupting_a": 1000, "max_c": 125, "ratings": ratings},
    }


def test_a_fuse_family_hands_back_one_rating():
    block = ElectricalBlock.model_validate(
        fuse_block(
            [
                {"rated_a": 2, "cold_mohm": 55.6, "melting_i2t_a2s": 9},
                {"rated_a": 5, "cold_mohm": 17.75, "melting_i2t_a2s": 37},
            ]
        )
    )
    assert block.fuse.rating(5).cold_resistance == pytest.approx(0.01775)
    with pytest.raises(KeyError, match="3 A.*2, 5"):
        block.fuse.rating(3)


def test_a_fuse_family_lists_each_rating_once():
    twice = {"rated_a": 2, "cold_mohm": 55.6, "melting_i2t_a2s": 9}
    with pytest.raises(ValidationError, match="2 A.*twice"):
        ElectricalBlock.model_validate(fuse_block([twice, twice]))


def wire(gauges):
    return {
        "type": "wire",
        "id": "test-silicone",
        "maker": "Test",
        "model": "Made-up silicone wire",
        "source": MADE_UP,
        "insulation_max_c": 200,
        "gauges": gauges,
    }


GAUGES = [
    {"awg": 12, "resistance_mohm_per_m": 5.2, "outer_diameter_mm": 3.8, "mass_g_per_m": 36},
    {"awg": 22, "resistance_mohm_per_m": 53, "outer_diameter_mm": 1.6, "mass_g_per_m": 5},
]


def test_a_wire_table_hands_back_a_gauge_in_si():
    table = Wire.model_validate(wire(GAUGES))
    assert table.gauge(12).resistance_per_m == pytest.approx(0.0052)
    assert table.gauge(22).outer_diameter == pytest.approx(0.0016)
    with pytest.raises(KeyError, match="18 AWG.*12, 22"):
        table.gauge(18)


def test_thicker_wire_has_less_resistance():
    backwards = [dict(GAUGES[0], resistance_mohm_per_m=60), GAUGES[1]]
    with pytest.raises(ValidationError, match="resistance"):
        Wire.model_validate(wire(backwards))


def test_a_wire_table_has_no_single_mass():
    with pytest.raises(AttributeError, match="per meter"):
        _ = Wire.model_validate(wire(GAUGES)).mass


def test_the_electrical_source_counts_as_one_of_the_parts_sources():
    part = Component.model_validate(
        {
            "type": "component",
            "id": "test-board",
            "maker": "Test",
            "model": "Board",
            "source": {"kind": "estimate", "note": "x"},
            "mass_g": 5,
            "electrical": board(),
        }
    )
    assert any(s.kind == "made_up" for s in part.sources())


def write_part(folder, data):
    folder.mkdir(parents=True, exist_ok=True)
    (folder / f"{data['id']}.yaml").write_text(yaml.safe_dump(data))


def component(part_id, electrical):
    return {
        "type": "component",
        "id": part_id,
        "maker": "Test",
        "model": part_id,
        "source": MADE_UP,
        "mass_g": 1,
        "electrical": electrical,
    }


def gh_family():
    return component(
        "test-gh",
        {"source": MADE_UP, "rating": {"continuous_a": 1.0, "wire_awg": 26, "max_c": 105}},
    )


def test_the_catalog_takes_a_board_whose_connectors_are_known(tmp_path):
    write_part(tmp_path / "components", gh_family())
    write_part(tmp_path / "components", component("test-board", board()))
    write_part(tmp_path / "wires", wire(GAUGES))
    catalog = load_catalog(tmp_path, allow_made_up=True)
    assert catalog.wire("test-silicone").gauge(22).awg == 22


def test_a_connector_family_that_isnt_in_the_catalog_fails(tmp_path):
    write_part(tmp_path / "components", component("test-board", board()))
    with pytest.raises(CatalogError, match="test-gh.*isn't in the catalog"):
        load_catalog(tmp_path, allow_made_up=True)


def test_a_connector_family_needs_a_rating(tmp_path):
    write_part(tmp_path / "components", component("test-gh", {"source": MADE_UP}))
    write_part(tmp_path / "components", component("test-board", board()))
    with pytest.raises(CatalogError, match="test-gh.*rating"):
        load_catalog(tmp_path, allow_made_up=True)
