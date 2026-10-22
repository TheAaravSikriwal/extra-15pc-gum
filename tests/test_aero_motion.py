"""The wind tunnel's flow moving (pcs14.aero.motion), from made-up snapshots written the way
FluidX3D's setup writes them: a steady wind, a wind that pulses, and the loop's seam."""

import numpy as np
import pytest

from pcs14.aero import motion

CELLS_PER_M = 100.0  # fine cells, 1 cm; snapshots 3 times coarser
U_MAX = 40.0


def write_snaps(folder, wind, count=16, seconds=0.1, size=(40, 90, 30), yaw=-90.0):
    """Snapshots of a box (x, y, z coarse cells) where the air goes along y at wind(t) m/s, the
    drone's origin at fine cell (60, 60, 45), and a plane 270 by 90 fine cells."""
    nx, ny, nz = size
    snaps = folder / "snaps"
    snaps.mkdir(parents=True, exist_ok=True)
    times = np.linspace(0.2, 0.2 + seconds, count)
    for k, t in enumerate(times):
        u = np.zeros((nz, ny, nx, 3))
        u[..., 1] = wind(t)
        (np.round(u / U_MAX * 32767)).astype("<i2").tofile(snaps / f"snap-{k:03d}.bin")
        plane = np.full((90, 270), wind(t))
        np.round(plane / U_MAX * 65535).astype("<u2").tofile(snaps / f"plane-{k:03d}.bin")
    (snaps / "times.txt").write_text("\n".join(f"{t:.6f}" for t in times) + "\n")
    (snaps / "snaps.txt").write_text(
        f"count = {count}\nnx = {nx}\nny = {ny}\nnz = {nz}\ncoarsen = 3\nx0 = 0\ny0 = 0\n"
        f"z0 = 0\ncells_per_m = {CELLS_PER_M}\nu_max = {U_MAX}\norigin_x = 60\norigin_y = 60\n"
        f"origin_z = 45\nyaw_deg = {yaw}\npitch_deg = 0\nspeed = 10\nplane_x = 60\n"
        "plane_ny = 270\nplane_nz = 90\n", encoding="utf-8")  # fmt: skip
    return folder


def test_a_case_without_snapshots_reads_as_none(tmp_path):
    assert motion.read_motion(tmp_path) is None


def test_the_snapshots_read_back_in_metres_from_the_drone(tmp_path):
    found = motion.read_motion(write_snaps(tmp_path, lambda t: 10.0))
    assert found.u.shape == (16, 30, 90, 40, 3)
    assert found.u[3, 5, 5, 5] == pytest.approx([0, 10, 0], abs=0.002)
    assert found.cell_m == pytest.approx(0.03)
    # the first coarse cell's middle is fine cell 1, 59 cells short of the origin's 60
    assert found.low == pytest.approx([-0.59, -0.59, -0.44])
    assert found.inside(np.array([[0.0, 0.0, 0.0], [0.0, 5.0, 0.0]])).tolist() == [True, False]


def test_a_particle_rides_the_wind_downstream_a_frame_at_a_time(tmp_path):
    found = motion.read_motion(write_snaps(tmp_path, lambda t: 10.0))
    loop = motion.Loop.of(found)
    assert loop.period == pytest.approx(0.08)  # the stretch, less the seam's ease
    seeds = np.array([[0.0, -0.5, 0.0], [0.1, -0.5, 0.1]])
    carried = motion.carry(found, loop, seeds, np.array([0, 10]))
    track = carried.tracks[0]
    dt = loop.period / motion.LOOP_FRAMES
    # nose into the wind: downstream is aft, -x in the drone's frame, 10 m/s of it
    assert np.diff(track[:, 0]) == pytest.approx(-10 * dt, abs=1e-4)
    assert carried.speeds[0] == pytest.approx(10.0, abs=0.01)
    # it leaves the box before its loop is up: 2.4 m of box at 10 m/s is 0.24 s, 0.08 s a loop
    assert len(track) == motion.LOOP_FRAMES
    assert carried.births.tolist() == [0, 10]


def test_the_loop_ends_where_it_starts(tmp_path):
    found = motion.read_motion(write_snaps(tmp_path, lambda t: 10.0 + 4 * np.sin(60 * t)))
    loop = motion.Loop.of(found)
    p = np.array([[0.0, 0.0, 0.0]])
    start = motion.velocity(found, loop, p, np.array([0.0]))
    end = motion.velocity(found, loop, p, np.array([loop.period - 1e-6]))
    assert end == pytest.approx(start, abs=0.01)
    # and past the seam it's the snapshots themselves
    mid = motion.velocity(found, loop, p, np.array([loop.blend + 0.01]))
    t = found.times[0] + loop.blend + 0.01
    assert mid[0][1] == pytest.approx(10.0 + 4 * np.sin(60 * t), abs=0.15)


def test_the_slice_plays_a_frame_for_each_of_the_loops(tmp_path):
    found = motion.read_motion(write_snaps(tmp_path, lambda t: 10.0))
    frames, corners = motion.plane_frames(found, motion.Loop.of(found), 17.0, (-0.5, 1.0),
                                          (0.3, -0.3), width=150)  # fmt: skip
    assert frames.shape == (motion.LOOP_FRAMES, 60, 150) and frames.dtype == np.uint8
    assert int(frames[5, 10, 10]) == round(10 / 17 * 255)
    # in the drone's frame, nose into the wind: the slice's along-the-wind edge runs fore and aft
    assert corners[0] == pytest.approx([0.5, 0.0, 0.3], abs=1e-9)
    assert corners[1] == pytest.approx([-1.0, 0.0, 0.3], abs=1e-9)


def test_the_particles_pack_into_bytes_the_site_reads(tmp_path):
    found = motion.read_motion(write_snaps(tmp_path, lambda t: 10.0))
    loop = motion.Loop.of(found)
    carried = motion.carry(found, loop, np.array([[0.0, -0.5, 0.0], [0.0, 9.0, 0.0]]),
                           np.array([3, 7]))  # fmt: skip
    data = motion.particle_bytes(carried, 17.0)
    count, frames, points = np.frombuffer(data[:12], dtype="<u4")
    assert (count, frames) == (2, motion.LOOP_FRAMES)
    births = np.frombuffer(data[12:16], dtype="<u2")
    lengths = np.frombuffer(data[16:20], dtype="<u2")
    assert births.tolist() == [3, 7]
    assert lengths.tolist() == [motion.LOOP_FRAMES, 0]  # the second starts outside the box
    mm = np.frombuffer(data[20 : 20 + points * 6], dtype="<i2").reshape(-1, 3)
    assert mm[0].tolist() == [500, 0, 0]  # 0.5 m ahead of the drone, in mm
    assert len(data) == 20 + points * 6 + points


def test_releases_in_a_wind_start_upstream_and_some_in_the_wake(tmp_path):
    found = motion.read_motion(write_snaps(tmp_path, lambda t: 10.0))
    low, high = np.array([-0.15, -0.1, -0.05]), np.array([0.15, 0.1, 0.05])
    seeds, births = motion.seeds_for(found, low, high, count=200)
    assert len(seeds) == 200 and births.min() >= 0 and births.max() < motion.LOOP_FRAMES
    upstream = seeds[:, 1] < low[1] - 0.3
    assert upstream.sum() == 200 - int(200 * motion.WAKE_SHARE)
    assert np.all(found.inside(seeds))
