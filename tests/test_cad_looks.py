"""The parts' looks (pcs14.cad.looks): the detail the pictures and the site's model show, each
drawn inside its part's envelope, so the checks, which use the envelopes, don't change."""

import math
from pathlib import Path

import pytest

from pcs14.catalog import load_catalog

ROOT = Path(__file__).resolve().parents[1]
MM = 0.001


@pytest.fixture(scope="module")
def catalog():
    return load_catalog(ROOT / "design" / "catalog")


def within(look, envelope, slack=0.0003):
    a, b = look.bounding_box(), envelope.bounding_box()
    return all(getattr(a.min, k) >= getattr(b.min, k) - slack for k in "XYZ") and all(
        getattr(a.max, k) <= getattr(b.max, k) + slack for k in "XYZ"
    )


def children(look) -> dict:
    return {c.label: c for c in look.children}


def test_a_board_has_its_board_chips_and_plugs_inside_its_envelope(catalog):
    from pcs14.cad.looks import look_for
    from pcs14.cad.parts import build_part

    fc = catalog.component("ark-fpv")
    look = look_for(fc)
    assert {"board", "chips", "plugs"} <= set(children(look))
    assert within(look, build_part(fc))
    # a JST plug where the pins research put the ESC port, on the +x edge
    plugs = children(look)["plugs"].solids()
    assert any(
        abs(s.center().X - 16.3 * MM) < 1 * MM and abs(s.center().Y + 4.5 * MM) < 1 * MM
        for s in plugs
    )


def test_a_breakout_gets_a_header_pin_at_each_of_its_pins(catalog):
    from pcs14.cad.looks import look_for
    from pcs14.cad.parts import build_part

    teensy = catalog.component("pjrc-teensy-41")
    look = look_for(teensy)
    pins = children(look)["pins"].solids()
    assert len(pins) == sum(len(c.pins) for c in teensy.cad.connectors)
    assert any(
        abs(s.center().X - 29.21 * MM) < 0.2 * MM and abs(s.center().Y + 7.62 * MM) < 0.2 * MM
        for s in pins
    )
    assert within(look, build_part(teensy))
    # a breakout drawn as a box in the catalog gets a board too
    imu = catalog.component("adafruit-lsm6dsox")
    assert {"board", "pins"} <= set(children(look_for(imu)))
    assert within(look_for(imu), build_part(imu))


def test_a_placeholder_keeps_its_plain_shape(catalog):
    from pcs14.cad.looks import look_for

    assert look_for(catalog.component("claws-placeholder")) is None  # no claw picked yet


def test_the_plain_boxes_and_tubes_get_looks_of_their_own(catalog):
    from pcs14.cad.looks import OWN_LOOKS, look_for
    from pcs14.cad.parts import build_part

    parts = {p.id: p for p in catalog.all_parts()}
    for part_id in OWN_LOOKS:
        look = look_for(parts[part_id])
        assert look is not None and within(look, build_part(parts[part_id])), part_id
    chute = children(look_for(parts["fruity-chutes-harrier-40-42"]))
    assert {"cap", "body"} <= set(chute)
    lidar = children(look_for(parts["benewake-tf-luna"]))
    assert len(lidar["lens"].solids()) == 2  # one window to send from, one to see with
    assert "fan" in children(look_for(parts["rpi-active-cooler"]))
    assert "shield" in children(look_for(parts["heltec-ht-hc01p"]))
    assert {"lens", "plugs"} <= set(children(look_for(parts["rpi-camera-module-3"])))
    assert {"nickel", "sleeve"} <= set(children(look_for(parts["branch-fuses"])))


def test_a_coupler_opens_toward_the_half_it_mates_with(catalog):
    from pcs14.cad.looks import look_for

    socket = children(look_for(catalog.component("module-socket")))["pins"].bounding_box()
    plug = children(look_for(catalog.component("module-plug")))["pins"].bounding_box()
    height = catalog.component("module-plug").cad.height_mm * MM
    # the socket's contacts sit just inside its bottom face, the plug's just inside its top
    assert socket.min.Z == pytest.approx(0.4 * MM, abs=1e-6)
    assert plug.max.Z == pytest.approx(height - 0.4 * MM, abs=1e-6)


def test_the_pack_is_welded_with_nickel_across_its_cell_ends(catalog):
    from pcs14.cad.parts import pack_layout, pack_look, pack_solid

    cell = catalog.cell("molicel-p45b")
    layout = pack_layout(cell, cells=12, max_length=0.150, max_width=0.090)
    look = pack_look(cell, layout)
    assert within(look, pack_solid(cell, layout), slack=1e-6)
    parts = children(look)
    assert len(parts["body"].solids()) == 12
    assert len(parts["nickel"].solids()) == (layout.along + 1) * layout.layers


def test_the_frames_screws_sit_flush_inside_it(catalog):
    from pcs14.cad.frame import build_frame

    model = build_frame(catalog.frame("iflight-nazgul-xl10-v6"))
    screws = children(model.look)["screws"]
    # the back standoffs' two each and each motor's four; the front standoffs stand past the
    # nose's edge, so a head there would hang off the plate
    assert len(screws.solids()) == 2 * 2 + 4 * 4
    assert within(model.look, model.solid, slack=1e-6)


def test_a_motor_has_its_base_the_gap_and_a_bell_with_cooling_holes(catalog):
    from pcs14.cad.looks import look_for
    from pcs14.cad.parts import build_part

    motor = catalog.motor("emax-e3-2814-850kv")
    look = look_for(motor)
    assert {"base", "bell", "shaft"} <= set(children(look))
    assert look.volume < 0.95 * build_part(motor).volume
    assert within(look, build_part(motor))


def test_the_blades_twist_flatter_toward_the_tip(catalog):
    from pcs14.cad.parts import blade_sections, prop_disk, prop_look

    prop = catalog.prop("gemfan-1050x3")
    sections = blade_sections(prop)
    angles = [s.angle_deg for s in sections]
    assert all(a > b for a, b in zip(angles, angles[1:], strict=False))
    # at each radius, the angle the pitch gives there
    for s in sections:
        assert s.angle_deg == pytest.approx(
            math.degrees(math.atan(prop.pitch / (2 * math.pi * s.radius)))
        )
    assert within(prop_look(prop), prop_disk(prop), slack=0.0005)


def test_the_mass_spread_keeps_the_flat_blades_the_flight_models_were_made_with(catalog):
    from pcs14.cad.parts import prop_disk, prop_solid

    prop = catalog.prop("gemfan-1050x3")
    solid = prop_solid(prop)
    assert within(solid, prop_disk(prop), slack=0.0005)
    # flat blades: three quarters out, every blade at the one pitch angle
    assert solid.volume > 0


def test_the_frames_arms_have_their_cutouts(catalog):
    from pcs14.cad.frame import build_frame

    model = build_frame(catalog.frame("iflight-nazgul-xl10-v6"))
    assert model.look.volume < model.solid.volume
    assert within(model.look, model.solid)


def test_the_model_draws_the_looks_and_the_checks_keep_the_envelopes():
    from build123d import Box

    from pcs14.cad.assembly import Piece
    from pcs14.cad.export import model_shapes

    envelope, look = Box(0.1, 0.1, 0.1), Box(0.05, 0.05, 0.05)
    plain = Piece("box", Box(0.1, 0.1, 0.1), "bought", "base", 0.1, 0.1)
    detailed = Piece("board", envelope, "bought", "base", 0.1, 0.1, look=look)
    shapes = model_shapes([plain, detailed])
    assert shapes[1] is look and shapes[1].label == "board"
    assert shapes[0] is plain.solid
    assert detailed.solid is envelope  # what the checks see


def test_every_look_stays_inside_its_envelope(catalog):
    from pcs14.cad.looks import look_for
    from pcs14.cad.parts import build_part

    looked = 0
    for part in catalog.all_parts():
        look = look_for(part)
        if look is None:
            continue
        looked += 1
        assert within(look, build_part(part)), part.id
    assert looked >= 25  # the boards, the breakouts, the motor and the plain parts' own
