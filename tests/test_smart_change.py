"""Change detection (#11): two orthomosaics of the same ground, differenced, and what changed
flagged as blobs on the map."""

import numpy as np

from pcs14.smart import change
from pcs14.smart.ortho import Mosaic


def two_maps():
    a = np.full((200, 200, 3), 95, dtype=np.uint8)
    a[40:52, 40:52] = (200, 80, 160)  # the box, before
    a[150:160, 120:126] = (60, 120, 70)  # a tree that stays put
    b = a.copy()
    b[40:52, 40:52] = 95  # gone from there...
    b[100:112, 150:162] = (200, 80, 160)  # ...and here now
    return Mosaic(a, 0.0, 20.0, 0.1, 1.0), Mosaic(b, 0.0, 20.0, 0.1, 1.0)


def test_a_moved_box_shows_up_where_it_was_and_where_it_went():
    before, after = two_maps()
    blobs = change.changes(before, after)
    assert len(blobs) == 2
    places = sorted((round(b.east, 1), round(b.north, 1)) for b in blobs)
    # where it was: columns 40 to 52, rows 40 to 52; where it went: columns 150 to 162
    assert places[0] == (4.6, 15.4) and places[1] == (15.6, 9.4)
    assert all(abs(b.area_m2 - 1.44) < 0.1 for b in blobs)


def test_specks_too_small_to_be_anything_are_left_out():
    before, after = two_maps()
    after.image[5, 5] = (255, 255, 255)
    assert len(change.changes(before, after)) == 2
