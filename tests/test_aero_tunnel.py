"""The wind tunnel's cases and stills: the case file FluidX3D reads, which way each prop turns,
and the stills composed from a made-up frame. FluidX3D itself only runs on the PC."""

import numpy as np
import pytest

from pcs14.aero import stills, tunnel


def made_up_props():
    return tuple(
        tunnel.Prop(f"p-{k}.stl", (x, y, 0.05), tunnel.spin_at(x, y))
        for k, (x, y) in enumerate(((0.16, -0.16), (-0.16, 0.16), (0.16, 0.16), (-0.16, -0.16)))
    )


def test_the_props_turn_the_way_px4s_quad_x_does():
    # front right and back left counterclockwise, front left and back right clockwise
    assert [p.spin for p in made_up_props()] == [1, 1, -1, -1]


def test_the_case_file_says_everything_fluidx3ds_setup_reads():
    cruise, crosswind, hover = tunnel.cases("Max", 3.2, 607.0, 0.127, made_up_props(), 0.16)
    text = cruise.text()
    for line in ("name = Max-cruise", "mode = tunnel", "body = max-body.stl", "speed = 10",
                 "yaw_deg = -90", "pitch_deg = 3.200", "props = 0"):  # fmt: skip
        assert line in text.splitlines(), line
    assert "yaw_deg = 0" in crosswind.text().splitlines()  # side on to the wind
    lines = hover.text().splitlines()
    assert "mode = hover" in lines and "speed = 0" in lines and "props = 4" in lines
    assert "prop_2_spin = -1" in lines and "omega = 607.000" in lines
    assert "slice_x_m = 0.16" in lines  # the slice through the front pair
    # the color scale: past the 10 m/s wind in the tunnel, the downwash's speed in the hover
    # (the props' 71 m/s tips used to set it, and the downwash came out dark)
    assert "color_max_m_s = 17" in cruise.text().splitlines()
    assert "color_max_m_s = 10" in lines
    assert hover.time_s >= 0.3  # long enough for the downwash to reach down past a meter


def test_a_crop_keeps_the_aspect_and_stays_inside():
    image = np.zeros((1440, 2560, 3))
    found = stills.crop(image, 0.8, focus=(0.1, 0.5))
    assert found.shape[1] / found.shape[0] == pytest.approx(0.8, abs=0.002)
    assert found.shape[0] == 1440  # as tall as the frame
    wide = stills.crop(image, 3.0)
    assert wide.shape[1] == 2560 and wide.shape[1] / wide.shape[0] == pytest.approx(3.0, abs=0.01)


@pytest.mark.parametrize("size", stills.SIZES)
def test_a_still_composes_in_every_post_size(tmp_path, size):
    import matplotlib.image as mpimg

    frame = tmp_path / "side-streamlines-000001.png"
    rng = np.random.default_rng(1)
    mpimg.imsave(frame, rng.random((144, 256, 3)))
    cruise = tunnel.cases("Max", 3.2, 607.0, 0.127, (), 0.0)[0]
    found = stills.draw(cruise, tmp_path, tmp_path / "out")
    assert len(found) == len(stills.SIZES)  # the one view there's a frame for, in every size
    assert all(p.stat().st_size > 10_000 for p in found)
    assert tunnel.frame(tmp_path, "side-streamlines") == frame
