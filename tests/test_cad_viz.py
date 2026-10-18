"""The CAD in Rerun: the build-up, the module combinations and the exploded view."""

import rerun.blueprint as rrb

from pcs14 import style


def pieces():
    from build123d import Box, Pos

    from pcs14.cad.assembly import Piece

    return [
        Piece("frame", Box(0.3, 0.03, 0.035), "frame", "base", 0.3, 0.3),
        Piece("pack", Pos(0, 0, -0.03) * Box(0.14, 0.065, 0.043), "pack", "base", 0.8, 0.8),
        Piece("v housing", Pos(0, 0, 0.07) * Box(0.06, 0.09, 0.07), "printed", "V", 0.04, 0.05),
    ]


def test_writes_a_cad_recording_without_a_viewer(tmp_path):
    from pcs14.viz.cad_log import CadRecorder

    path = tmp_path / "cad.rrd"
    recorder = CadRecorder(path)
    parts = pieces()
    recorder.log_pieces(parts)
    recorder.log_build_up([p.name for p in parts])
    recorder.log_combination(
        step=10,
        label="base",
        shown={"frame", "pack"},
        all_names=[p.name for p in parts],
        pack_shift=-0.01,
        center=(0.002, 0.0, 0.01),
        thrust=(0.0, 0.0, 0.045),
        problems=[parts[2]],
        passed=False,
    )
    recorder.log_explode(start=20, pieces=parts)
    recorder.log_summary("all good")
    recorder.close()
    assert path.stat().st_size > 1000


def test_the_3d_view_opens_on_the_projects_black_background():
    from pcs14.viz.cad_log import cad_blueprint

    blueprint = cad_blueprint()
    views = []

    def walk(item):
        for child in getattr(item, "contents", []):
            views.append(child)
            walk(child)

    walk(blueprint.root_container)
    spatial = [v for v in views if isinstance(v, rrb.Spatial3DView)]
    assert len(spatial) == 1
    background = repr(spatial[0].properties.get("Background"))
    r, g, b = style.rgb("background")
    assert (
        f"{(r << 24) | (g << 16) | (b << 8) | 255}" in background or "0B0B0B" in background.upper()
    )
