"""The wind tunnel's page data: its stills with what each says, and each case's frames along
the way, from a made-up tunnel output folder."""

import json

import numpy as np
from PIL import Image

from pcs14.aero import tunnel
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


def test_the_tunnel_page_gets_its_stills_and_its_frames_in_order(tmp_path):
    made_up_tunnel(tmp_path / "tunnel")
    out = tmp_path / "data"
    found = tunnel_data(tmp_path / "tunnel", out)
    (still,) = found.stills
    assert still.title == "The drag lines" and still.case == "Max-cruise"
    assert still.file == "tunnel/Max-cruise-side-streamlines.jpg"  # the wide one
    assert (out / still.file).is_file()
    (case,) = found.cases  # the hover has no frames yet
    assert case.name == "Max-cruise" and case.label == "Cruise"
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
