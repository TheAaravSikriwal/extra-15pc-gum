"""The wind tunnel's averaged flow (pcs14.aero.flow), from a made-up one written the way
FluidX3D's setup writes it: a steady wind with a block in its way where the drone is."""

import numpy as np
import pytest

from pcs14.aero import flow, motion

CELLS_PER_M = 100.0  # fine cells; coarsened by 2, a coarse cell is 2 cm


def write_field(folder, u, solid, origin_fine, yaw=-90.0, pitch=0.0, speed=10.0):
    nz, ny, nx = solid.shape
    folder.mkdir(parents=True, exist_ok=True)
    u.astype("<f4").tofile(folder / "field.bin")
    (solid * 255).astype(np.uint8).tofile(folder / "solid.bin")
    ox, oy, oz = origin_fine
    lines = [f"nx = {nx}", f"ny = {ny}", f"nz = {nz}", "coarsen = 2",
             f"cells_per_m = {CELLS_PER_M}", f"origin_x = {ox}", f"origin_y = {oy}",
             f"origin_z = {oz}", f"yaw_deg = {yaw}", f"pitch_deg = {pitch}", f"speed = {speed}",
             "samples = 16", "force_x_n = 0.1", "force_y_n = 1.5", "force_z_n = -0.2"]  # fmt: skip
    (folder / "field.txt").write_text("# made up\n" + "\n".join(lines) + "\n", encoding="utf-8")
    return folder


def wind_with_a_block(tmp_path, speed=10.0):
    """A 10 m/s wind along y through a 60 x 120 x 50 cell box (2 cm cells), and a 20 cm block
    in it where the drone is, with the air going round its sides."""
    nz, ny, nx = 50, 120, 60
    u = np.zeros((nz, ny, nx, 3))
    u[..., 1] = speed
    solid = np.zeros((nz, ny, nx))
    solid[20:30, 40:50, 25:35] = 1.0
    u[solid > 0] = 0.0
    # the drone's origin in the middle of the block, in fine cells
    return write_field(tmp_path / "case", u, solid, (61.0, 91.0, 51.0), speed=speed)


def test_a_case_without_its_flow_reads_as_none(tmp_path):
    assert flow.read_field(tmp_path) is None


def test_the_drones_frame_and_the_tunnels_go_both_ways():
    turn = flow.rotation(-90.0, 3.0)
    # nose into the wind: the drone's forward points up the tunnel, against the wind (-y)
    tilt = np.radians(3)
    assert turn @ np.array([1.0, 0, 0]) == pytest.approx(
        [0, -np.cos(tilt), -np.sin(tilt)], abs=1e-9
    )
    # its top into the wind, nose down, and its belly the other way
    assert flow.rotation(-90.0, 90.0) @ np.array([0, 0, 1.0]) == pytest.approx([0, -1, 0], abs=1e-9)
    assert flow.rotation(-90.0, -90.0) @ np.array([0, 0, 1.0]) == pytest.approx([0, 1, 0], abs=1e-9)
    # side on, its left points downwind
    assert flow.rotation(0.0, 0.0) @ np.array([0, 1.0, 0]) == pytest.approx([0, 1, 0])


def test_a_field_reads_back_with_the_drone_where_it_was(tmp_path):
    field = flow.read_field(wind_with_a_block(tmp_path))
    assert field.cell_m == pytest.approx(0.02)
    assert field.u.shape == (50, 120, 60, 3)
    # the origin (fine cell 61) is coarse cell 30.25, in the block's middle
    assert field.origin == pytest.approx([30.25, 45.25, 25.25])
    back = field.to_cells(field.to_drone(np.array([[3.0, 7.0, 9.0]])))
    assert back[0] == pytest.approx([3.0, 7.0, 9.0])
    low, high = motion.outline_in_tunnel(field)
    assert np.all(high - low < 0.25) and np.all(high - low > 0.15)  # the 20 cm block
    assert field.force == pytest.approx([0.1, 1.5, -0.2])
