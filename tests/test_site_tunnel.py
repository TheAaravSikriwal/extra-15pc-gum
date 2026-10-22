"""The wind tunnel's page data: its stills with what each says, and each case's frames along
the way, from a made-up tunnel output folder."""

import json

import numpy as np
import pytest
from PIL import Image

from pcs14.aero import motion, tunnel
from pcs14.site import schema
from pcs14.site.tunnel import tunnel_data, write_tunnel


def made_up_tunnel(folder):
    stills = folder / "stills"
    stills.mkdir(parents=True)
    rng = np.random.default_rng(2)
    for size in ("portrait", "wide"):
        Image.fromarray((rng.random((108, 192, 3)) * 255).astype("uint8")).save(
            stills / f"Max-cruise-side-streamlines-{size}.png")  # fmt: skip
    said = {"Max-cruise-side-streamlines": {
        "case": "Max-cruise", "view": "side-streamlines", "title": "The drag lines",
        "subtitle": "10 m/s", "number": "10 m/s", "caption": "A picture, not a measurement",
    }}  # fmt: skip
    (stills / "stills.json").write_text(json.dumps(said), encoding="utf-8")
    run = folder / "Max-cruise"
    run.mkdir()
    (run / "frames.txt").write_text("300 0.03\n100 0.01\n200 0.02\n", encoding="utf-8")
    for step in (100, 200, 300):
        for view in tunnel.PLAY_VIEWS:
            Image.fromarray((rng.random((1080, 1920, 3)) * 255).astype("uint8")).save(
                run / f"play-{view}-{step:09d}.png")  # fmt: skip
    (folder / "Max-hover").mkdir()  # a case run before the frames: stills only
    (folder / "Max-crosswind").mkdir()
    (folder / "Max-crosswind" / "frames.txt").write_text("100 0.01\n", encoding="utf-8")
    Image.fromarray((rng.random((108, 192, 3)) * 255).astype("uint8")).save(
        folder / "Max-crosswind" / "play-side-speed-000000100.png")  # fmt: skip


def test_the_tunnel_page_gets_its_stills_and_its_frames_in_order(tmp_path):
    made_up_tunnel(tmp_path / "tunnel")
    out = tmp_path / "data"
    found = tunnel_data(tmp_path / "tunnel", out)
    (still,) = found.stills
    assert still.title == "The drag lines" and still.case == "Max-cruise"
    assert still.file == "tunnel/Max-cruise-side-streamlines.jpg"  # the wide one
    assert (out / still.file).is_file()
    case, crosswind = found.cases  # the hover has no frames yet
    assert case.name == "Max-cruise" and case.label == "Cruise"
    assert crosswind.label == "Crosswind"  # after the cruise, not before it
    assert [f.step for f in case.frames] == [100, 200, 300]
    assert [f.t_s for f in case.frames] == [0.01, 0.02, 0.03]
    first = out / case.frames[0].files["side-speed"]
    assert first.is_file() and first.suffix == ".jpg"
    with Image.open(first) as image:
        assert image.width == 960  # thinned for the page
    # FluidX3D's license wants the altered source published before any results are
    assert found.fork_public is False and "fork" in found.note


def test_the_tunnel_data_passes_the_schema(tmp_path):
    made_up_tunnel(tmp_path / "tunnel")
    (path,) = [p for p in write_tunnel(tmp_path / "data", tmp_path / "tunnel")
               if p.suffix == ".json"]  # fmt: skip
    found = schema.Tunnel.model_validate_json(path.read_text(encoding="utf-8"))
    assert found.schema_version == schema.SCHEMA_VERSION
    assert (tmp_path / "data" / "tunnel.js").is_file()  # for a page opened from disk


def test_no_tunnel_runs_is_an_empty_page(tmp_path):
    found = tunnel_data(tmp_path / "nothing", tmp_path / "data")
    assert found.stills == [] and found.cases == []


def settings_file(path, values: dict):
    path.write_text("".join(f"{k} = {v}\n" for k, v in values.items()), encoding="utf-8")


def made_up_flow(folder, name="Max-cruise"):
    """A case folder with a made-up flow: its average and its snapshots, a 10 m/s wind and a
    block where the drone is."""
    nz, ny, nx = 40, 90, 40
    u = np.zeros((nz, ny, nx, 3))
    u[..., 1] = 10.0
    solid = np.zeros((nz, ny, nx))
    solid[16:24, 30:38, 16:24] = 1.0
    u[solid > 0] = 0.0
    run = folder / name
    snaps = run / "snaps"
    snaps.mkdir(parents=True, exist_ok=True)
    u.astype("<f4").tofile(run / "field.bin")
    (solid * 255).astype(np.uint8).tofile(run / "solid.bin")
    turned = {"yaw_deg": -90, "pitch_deg": 3, "speed": 10}
    grid = {"nx": 40, "ny": 90, "nz": 40}
    settings_file(run / "field.txt", {**grid, "coarsen": 2, "cells_per_m": 100, "origin_x": 41,
                                       "origin_y": 69, "origin_z": 41, **turned, "samples": 16,
                                       "force_x_n": 0.01, "force_y_n": 1.84,
                                       "force_z_n": -0.1})  # fmt: skip
    # the snapshots: the same flow on 2 cm cells, sixteen times over a tenth of a second
    times = np.linspace(0.3, 0.4, 16)
    plane = np.full((40, 90), 10.0)
    plane[:, 38:] = 4.0  # a slow wake behind the block
    for k in range(16):
        np.round(u / 40 * 32767).astype("<i2").tofile(snaps / f"snap-{k:03d}.bin")
        np.round(plane / 40 * 65535).astype("<u2").tofile(snaps / f"plane-{k:03d}.bin")
    (snaps / "times.txt").write_text(" ".join(f"{t:.6f}" for t in times), encoding="utf-8")
    settings_file(snaps / "snaps.txt", {"count": 16, "nx": 40, "ny": 90, "nz": 40, "coarsen": 1,
                                         "x0": 0, "y0": 0, "z0": 0, "cells_per_m": 50, "u_max": 40,
                                         "origin_x": 20.5, "origin_y": 34.5, "origin_z": 20.5,
                                         **turned, "plane_x": 20, "plane_ny": 90,
                                         "plane_nz": 40})  # fmt: skip
    settings_file(run / "case.txt", {"name": name, "color_max_m_s": 17, "pitch_deg": 3,
                                      "props": 0})  # fmt: skip
    return run


def test_each_case_with_its_flow_gets_particles_and_a_slice_for_the_drone_view(tmp_path):
    made_up_tunnel(tmp_path / "tunnel")
    made_up_flow(tmp_path / "tunnel", "Max-left")
    made_up_flow(tmp_path / "tunnel", "Max-cruise")
    out = tmp_path / "data"
    found = tunnel_data(tmp_path / "tunnel", out)
    # in the drone view's order: the front first, whatever the folders' names
    run = [(f.direction, f.label) for f in found.flows if f.file]
    assert run == [("front", "From the front"), ("left", "From the left")]
    # and every other way the air comes, listed but not run yet
    assert [f.direction for f in found.flows] == list(tunnel.DIRECTIONS)
    assert [f.file for f in found.flows if f.direction == "above"] == [None]
    entry = found.flows[0]
    data = schema.TunnelFlow.model_validate_json((out / entry.file).read_text(encoding="utf-8"))
    assert data.direction == "front" and data.setup == "Max" and data.speed == 10
    assert data.force_n == 1.84  # along the wind, FluidX3D's own (visual-grade) number
    assert data.pitch_deg == 3.0  # the tilt it cruises with
    assert data.frames == motion.LOOP_FRAMES and data.loop_s == pytest.approx(0.08)
    particles = (out / data.particles.file).read_bytes()
    count, frames, _ = np.frombuffer(particles[:12], dtype="<u4")
    assert count == data.particles.count == motion.PARTICLES and frames == data.frames
    assert (out / f"{data.particles.file}.js").is_file()  # for a page opened from disk
    frames_bytes = (out / data.slice.file).read_bytes()
    assert len(frames_bytes) == data.frames * data.slice.width * data.slice.height
    assert len(data.slice.corners) == 4
