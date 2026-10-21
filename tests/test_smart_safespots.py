"""Safe spots: open ground, level, and clear of anything the drone could hit, on a height map;
and the nearest one to where it was asked to land. Worked by hand."""

import numpy as np
import pytest

from pcs14.smart import safespots

AREA = ((-20.0, 20.0), (0.0, 40.0))


def test_a_box_on_the_height_map_stands_where_it_is():
    heights = safespots.height_map([((5.0, 20.0, 1.5), (4.0, 3.0, 3.0))], AREA, 0.25)
    assert heights.at(east=5.0, north=20.0) == pytest.approx(3.0)
    assert heights.at(east=-10.0, north=10.0) == 0.0


def test_the_safe_ground_keeps_its_distance_from_the_box():
    heights = safespots.height_map([((5.0, 20.0, 1.5), (4.0, 3.0, 3.0))], AREA, 0.25)
    safe = safespots.safe(heights, footprint_m=0.6, clearance_m=3.0)
    assert not safe.at(east=5.0, north=20.0)  # on the box
    assert not safe.at(east=5.0 + 2.0 + 3.0, north=20.0)  # 3 m off its side, less the footprint
    assert safe.at(east=5.0 + 2.0 + 3.6 + 0.3, north=20.0)  # past footprint and clearance
    assert safe.at(east=-10.0, north=10.0)


def test_asked_to_land_on_the_box_it_picks_the_nearest_open_ground():
    heights = safespots.height_map([((5.0, 20.0, 1.5), (4.0, 3.0, 3.0))], AREA, 0.25)
    safe = safespots.safe(heights, footprint_m=0.6, clearance_m=3.0)
    east, north = safespots.nearest(safe, east=5.0, north=20.0)
    # out of the box's short side: 1.5 m half-width, then 3.6 m of footprint and clearance
    assert abs(north - 20.0) == pytest.approx(1.5 + 3.6, abs=0.3)
    assert safe.at(east=east, north=north)


def test_the_maps_obstacles_are_whatever_isnt_the_grounds_color():
    picture = np.full((40, 40, 3), 95, dtype=np.uint8)
    picture[10:14, 20:24] = (200, 80, 160)
    found = safespots.obstacles_from_picture(picture, ground=(95, 95, 95), tolerance=30)
    assert found[12, 22] and not found[30, 5]
