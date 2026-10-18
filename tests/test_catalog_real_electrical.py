"""The real catalog's electrical blocks: every part the connection list needs is there, every
number has a dated source, and the numbers agree with each other where they overlap."""

from pathlib import Path

import pytest

from pcs14.catalog import load_catalog

ROOT = Path(__file__).resolve().parents[1]

# Everything that carries current in the electrical design, old parts and new
ELECTRICAL = [
    "ark-fpv",
    "ark-gps",
    "ark-cannode",
    "radiomaster-rp2-v2",
    "benewake-tf-luna",
    "pjrc-teensy-41",
    "safety-monitor-buffers",
    "cjmcu-5018",
    "pololu-d36v6f3",
    "adafruit-lsm6dsox",
    "bat54c-on-adapter",
    "matek-bec12s-pro",
    "rpi-5-4gb",
    "rpi-active-cooler",
    "rpi-camera-module-3",
    "heltec-ht-hc01p",
    "fruity-chutes-harrier-40-42",
    "p-chute-switch",
    "p-servo-diodes",
    "claws-placeholder",
    "module-socket",
    "module-plug",
]
FAMILIES = ["amass-xt60", "amass-xt30", "jst-gh", "jst-sh"]


@pytest.fixture(scope="module")
def catalog():
    return load_catalog(ROOT / "design" / "catalog")


def blocks(catalog):
    return [(p.id, p.electrical) for p in catalog.all_parts() if p.electrical is not None]


@pytest.mark.parametrize("part_id", ELECTRICAL)
def test_every_electrical_part_has_a_block(catalog, part_id):
    assert catalog.component(part_id).electrical is not None


def test_the_esc_and_motor_have_blocks(catalog):
    assert catalog.esc("holybro-tekko32-f4-50a").electrical is not None
    assert catalog.motor("emax-e3-2814-850kv").electrical is not None


def test_the_diodes_know_their_drop(catalog):
    servo = catalog.component("p-servo-diodes").electrical.diode
    teensy = catalog.component("bat54c-on-adapter").electrical.diode
    assert servo.forward_volts(0.45) == pytest.approx(0.40, abs=0.01)  # a stalled servo
    assert teensy.forward_volts(0.1) == pytest.approx(0.8)


@pytest.mark.parametrize("family", FAMILIES)
def test_connector_families_carry_a_rating(catalog, family):
    assert catalog.component(family).electrical.rating is not None


def test_every_electrical_source_is_dated(catalog):
    undated = [part_id for part_id, block in blocks(catalog) if block.source.checked is None]
    assert undated == []


def test_draws_agree_with_the_power_the_sizing_model_uses(catalog):
    """Where a plain load (no supply of its own) has both, its typical draw times its voltage
    should land near power_w, which the sizing model counts against the battery."""
    for part in catalog.components.values():
        block = part.electrical
        if block is None or not block.draws or block.outputs or part.power_w == 0:
            continue
        watts = 0.0
        for draw in block.draws:
            volts = block.pin(draw.pin).volts or (draw.min_v + draw.max_v) / 2
            watts += draw.typical_a * volts
        assert watts == pytest.approx(part.power_w, rel=0.35, abs=0.15), part.id


def test_the_flight_controller_has_room_on_its_5v(catalog):
    supply = catalog.component("ark-fpv").electrical.output("5V")
    assert supply.continuous_a == 2.0 and supply.available == pytest.approx(1.5)


def test_the_dshot_lines_go_both_ways_at_both_ends(catalog):
    fc = catalog.component("ark-fpv").electrical
    esc = catalog.esc("holybro-tekko32-f4-50a").electrical
    for n in range(1, 5):
        assert fc.pin(f"ESC.CH{n}").direction == "both"
        assert esc.pin(f"FC.M{n}").direction == "both"


def test_the_teensy_pins_are_3v3_only(catalog):
    teensy = catalog.component("pjrc-teensy-41").electrical
    signals = [pin for _, pin in teensy.pins() if pin.role == "signal"]
    assert len(signals) == 42
    assert all(pin.max_volts == 3.3 for pin in signals)


def test_silicone_wire_resistance_sits_just_above_the_copper_standard(catalog):
    """UL3135's maximums (stranded, tinned) should be a little above NBS's solid copper."""
    silicone = catalog.wire("ul3135-silicone")
    standard = catalog.wire("bare-copper")
    for gauge in standard.gauges:
        if gauge.awg in {g.awg for g in silicone.gauges}:
            ratio = silicone.gauge(gauge.awg).resistance_per_m / gauge.resistance_per_m
            assert 1.0 <= ratio <= 1.15, gauge.awg
