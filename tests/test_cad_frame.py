"""The frame: iFlight's XL10 V6 from its published numbers and the outlines traced from its
top-down render. The nose points along +x, and z = 0 is the underside of the bottom plate."""

import math
from pathlib import Path

import pytest

from pcs14.catalog import load_catalog

ROOT = Path(__file__).resolve().parents[1]
MM = 0.001
CARBON_G_PER_CM3 = 1.6  # carbon fiber plate, roughly 1.5 to 1.6


@pytest.fixture(scope="module")
def frame():
    from pcs14.cad.frame import build_frame

    catalog = load_catalog(ROOT / "design" / "catalog")
    return build_frame(catalog.frame("iflight-nazgul-xl10-v6"))


def test_the_motors_sit_on_a_true_x_with_a_420_mm_wheelbase(frame):
    half = 420 / 2 / math.sqrt(2)
    spots = sorted((x / MM, y / MM) for x, y, _ in frame.motor_mounts)
    expected = sorted([(half, half), (half, -half), (-half, half), (-half, -half)])
    for got, want in zip(spots, expected, strict=True):
        assert got == pytest.approx(want, abs=0.01)
    pairs = [(a, b) for a in frame.motor_mounts for b in frame.motor_mounts]
    longest = max(math.dist(a[:2], b[:2]) for a, b in pairs)
    assert longest / MM == pytest.approx(420, abs=0.01)  # the diagonal
    nearest = min(math.dist(a[:2], b[:2]) for a, b in pairs if a != b)
    assert nearest / MM == pytest.approx(297, abs=0.1)  # neighbors, like iFlight's 297 x 297


def test_the_plates_and_arms_stack_up_to_35_mm(frame):
    assert frame.motor_mounts[0][2] / MM == pytest.approx(3 + 7)  # motors sit on the arms
    assert frame.bay_floor / MM == pytest.approx(3 + 7 + 3)
    assert frame.bay_height / MM == pytest.approx(19)
    assert frame.top / MM == pytest.approx(35)
    box = frame.solid.bounding_box()
    assert box.min.Z == pytest.approx(0, abs=1e-9)
    assert box.max.Z / MM == pytest.approx(35)


def test_the_body_reaches_further_forward_than_back(frame):
    box = frame.body.bounding_box()
    assert box.max.X / MM == pytest.approx(154)
    assert box.min.X / MM == pytest.approx(-62)
    assert box.size.Y / MM == pytest.approx(36)


def test_its_carbon_weighs_about_what_iflight_says(frame):
    grams = frame.carbon.volume * 1e6 * CARBON_G_PER_CM3
    # 343 g includes screws, standoffs and printed parts, so the carbon comes in under it
    assert 0.75 * 343 <= grams <= 343
