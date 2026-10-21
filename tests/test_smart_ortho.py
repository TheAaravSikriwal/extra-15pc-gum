"""Mapping (#7): an orthomosaic from camera frames and the poses they were taken from. The test
renders frames of a made-up ground through the same camera model, then puts them back
together."""

import numpy as np
import pytest

from pcs14.smart import ortho


def made_up_ground(size_m=40.0, px_per_m=4):
    n = int(size_m * px_per_m)
    ground = np.full((n, n, 3), 90, dtype=np.uint8)
    ground[40:60, 100:120] = (230, 80, 160)  # a magenta patch
    ground[100:130, 30:50] = (60, 120, 70)  # a green one
    return ground, px_per_m


def render(ground, px_per_m, camera, pose):
    """What the camera sees of a flat ground with `ground` as its picture (x east, y north)."""
    h, w = camera.height, camera.width
    rays = camera.rays(pose)  # (h*w, 3) in the world
    origin = pose.position
    t = -origin[2] / rays[:, 2]
    hit = origin + rays * t[:, None]
    col = (hit[:, 0] * px_per_m).astype(int)
    row = (ground.shape[0] - 1 - hit[:, 1] * px_per_m).astype(int)
    inside = (t > 0) & (col >= 0) & (col < ground.shape[1]) & (row >= 0) & (row < ground.shape[0])
    image = np.zeros((h * w, 3), dtype=np.uint8)
    image[inside] = ground[row[inside], col[inside]]
    return image.reshape(h, w, 3)


def test_a_point_straight_below_lands_in_the_middle_of_the_picture():
    camera = ortho.Camera(width=160, height=90, hfov_rad=1.15192)
    pose = ortho.Pose(position=np.array([20.0, 20.0, 30.0]), down=True)
    row, col = camera.project(pose, np.array([[20.0, 20.0, 0.0]]))
    assert row[0] == pytest.approx(44.5, abs=0.6) and col[0] == pytest.approx(79.5, abs=0.6)


def test_frames_put_back_together_make_the_ground_again():
    ground, px_per_m = made_up_ground()
    camera = ortho.Camera(width=160, height=90, hfov_rad=1.15192)
    frames = []
    for north in (10.0, 20.0, 30.0):
        for east in (10.0, 20.0, 30.0):
            pose = ortho.Pose(position=np.array([east, north, 25.0]), down=True)
            frames.append((render(ground, px_per_m, camera, pose), pose))
    mosaic = ortho.mosaic(frames, camera, east=(0.0, 40.0), north=(0.0, 40.0), m_per_px=0.25)
    # the magenta patch sits at east 25 to 30 m, north 25 to 30 m (rows from the top)
    patch = mosaic.color_at(east=27.5, north=27.5)
    assert patch[0] > 180 and patch[2] > 120 and patch[1] < 120
    assert mosaic.color_at(east=10.0, north=5.0)[1] == pytest.approx(90, abs=10)
    assert mosaic.covered > 0.8
    # a meter off the patch's corner, the nearest magenta within a meter is still the patch
    near = mosaic.nearest_color(east=24.0, north=24.0, color=(230, 80, 160), within_m=1.5)
    assert near[0] > 180


def test_a_camera_tipped_straight_down_on_a_drone_facing_north_is_the_nadir_view():
    import math

    s = math.sqrt(0.5)
    pose = ortho.Pose.on_drone((0.0, 0.0, 30.0), (0.0, 0.0, s, s), pitch_rad=math.pi / 2)
    assert np.allclose(pose.rotation, ortho.NADIR, atol=1e-9)
