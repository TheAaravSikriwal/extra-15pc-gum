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
    found = tunnel.cases("Max", 3.2, 607.0, 0.127, made_up_props(), 0.16, hover_thrust_n=5.8)
    cruise, crosswind, hover = found[0], found[2], found[-1]
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
    assert "color_max_m_s = 15" in lines
    assert hover.time_s >= 0.3  # long enough for the downwash to reach down past a meter
    # the props as actuator disks: at this resolution spinning blades are flat paddles that
    # fling the air sideways (2026-10-20), so each disk pushes its share of the weight down
    assert "rotor = disk" in lines and "thrust_n = 5.8" in lines
    assert "rotor = disk" not in cruise.text().splitlines()
    # and frames along the way, for the project site to play the flow back
    assert f"frames = {tunnel.PLAY_FRAMES}" in lines
    # and the averaged flow, over the last 40% of the run
    assert "field = 1" in lines and "field_from_s = 0.24" in lines and "field_coarsen = 2" in lines
    # and the flow moving, in a box reaching down into the downwash, over the run's last half
    assert "snap_count = 64" in lines and "snap_from_s = 0.2" in lines
    assert "snap_z0 = -1.6" in lines and "snap_y1 = 0.5" in lines
    assert "snap_y1 = 1.6" in cruise.text().splitlines()  # well behind it, for the wake


def test_the_air_meets_it_from_six_ways_and_in_the_hover():
    found = tunnel.cases("Max", 3.2, 607.0, 0.127, made_up_props(), 0.16, hover_thrust_n=5.8)
    by = {c.direction: c for c in found}
    assert list(by) == list(tunnel.DIRECTIONS)
    assert len({c.name for c in found}) == 7
    # the nose into the wind pitched forward, the tail into it pitched back, each side, and the
    # top and the belly into it; the side, back and vertical cases are the body alone
    turned = {d: (c.yaw_deg, c.pitch_deg) for d, c in by.items()}
    assert turned["front"] == (-90.0, 3.2) and turned["back"] == (90.0, -3.2)
    assert turned["right"] == (0.0, 0.0) and turned["left"] == (180.0, 0.0)
    assert turned["above"] == (-90.0, 90.0) and turned["below"] == (-90.0, -90.0)
    assert all(c.mode == "tunnel" and not c.props for d, c in by.items() if d != "hover")
    # only the cruise, the crosswind and the hover make stills for posts
    assert [d for d, c in by.items() if stills.stills_for(c)] == ["front", "right", "hover"]


def test_the_frames_along_the_way_come_in_order_with_their_times(tmp_path):
    # FluidX3D's setup lists each playback frame's time step and time in frames.txt
    (tmp_path / "frames.txt").write_text("200 0.02\n100 0.01\n", encoding="utf-8")
    for step in (100, 200):
        for view in tunnel.PLAY_VIEWS:
            (tmp_path / f"play-{view}-{step:09d}.png").write_bytes(b"png")
    found = tunnel.playback(tmp_path)
    assert [f.step for f in found] == [100, 200]
    assert found[0].seconds == 0.01
    assert set(found[0].files) == set(tunnel.PLAY_VIEWS)
    assert found[1].files["side-speed"].name == "play-side-speed-000000200.png"
    assert tunnel.playback(tmp_path / "not-run") == []


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
    # and what each still says, for the project site's tunnel page
    import json

    said = json.loads((tmp_path / "out" / "stills.json").read_text(encoding="utf-8"))
    entry = said[f"{cruise.name}-side-streamlines"]
    assert entry["case"] == cruise.name and entry["title"] == "The drag lines"
    assert "OpenFOAM" in entry["caption"]
