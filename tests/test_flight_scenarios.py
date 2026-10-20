"""The scenario scripts' own helpers, without Gazebo."""

import pytest

from pcs14.flight.scenarios import capability


def test_the_box_goes_where_the_claws_would_hold_it():
    # the drone level, its origin 1.6 m up and 0.0742 m above its feet
    x, y, z = capability.claws_position((1.0, 4.0, 1.6), lift_off=0.0742)
    assert (x, y) == (1.0, 4.0)
    gap = 1.6 - 0.0742 - (z + capability.PAYLOAD_SIZE / 2)  # feet to the box's top
    assert gap == pytest.approx(capability.CLAW_GAP)
