"""GPS-free flight's estimate (#24): optical flow between frames, the drone's attitude and the
rangefinder's height, turned into a position without GPS. Tested on frames rendered from a
made-up textured ground along a known path."""

import numpy as np
import pytest

from pcs14.smart import flow, ortho


def textured_ground(size_m=120.0, px_per_m=10, seed=3):
    from scipy.ndimage import gaussian_filter

    rng = np.random.default_rng(seed)
    n = int(size_m * px_per_m)
    noise = sum(
        gaussian_filter(rng.random((n, n)), s) * w for s, w in ((2, 1.0), (8, 2.0), (30, 3.0))
    )
    noise = (noise - noise.min()) / (noise.max() - noise.min())
    return (np.stack([noise] * 3, axis=2) * 200 + 30).astype(np.uint8), px_per_m


def render(ground, px_per_m, camera, pose, offset=60.0):
    rays = camera.rays(pose)
    t = -pose.position[2] / rays[:, 2]
    hit = pose.position + rays * t[:, None]
    col = ((hit[:, 0] + offset) * px_per_m).astype(int)
    row = (ground.shape[0] - 1 - (hit[:, 1] + offset) * px_per_m).astype(int)
    ok = (col >= 0) & (col < ground.shape[1]) & (row >= 0) & (row < ground.shape[0])
    image = np.zeros((rays.shape[0], 3), dtype=np.uint8)
    image[ok] = ground[row[ok], col[ok]]
    return image.reshape(camera.height, camera.width, 3)


def test_the_shift_between_two_frames_is_found_to_a_fraction_of_a_pixel():
    rng = np.random.default_rng(1)
    a = rng.random((120, 160))
    b = np.roll(a, (3, -5), axis=(0, 1))
    dy, dx = flow.shift(a, b)
    assert dy == pytest.approx(3.0, abs=0.1) and dx == pytest.approx(-5.0, abs=0.1)


def test_a_flown_path_comes_back_out_of_its_frames():
    ground, px_per_m = textured_ground()
    camera = ortho.Camera(width=320, height=180, hfov_rad=1.15192)
    level = np.array([0.0, 0.0, np.sqrt(0.5), np.sqrt(0.5)])  # facing north, level
    path = [(0.4 * k, 0.6 * k, 20.0) for k in range(60)]  # 0.72 m a frame, north-east-ish
    frames = []
    for east, north, up in path:
        pose = ortho.Pose.on_drone((east, north, up), level, pitch_rad=np.pi / 2)
        frames.append(render(ground, px_per_m, camera, pose))
    found = flow.track(frames, [level] * len(frames), [p[2] for p in path], camera,
                       pitch_rad=np.pi / 2)  # fmt: skip
    end = found[-1]
    truth = np.array(path[-1][:2])
    distance = np.hypot(*truth)
    assert np.hypot(*(end - truth)) < 0.05 * distance
