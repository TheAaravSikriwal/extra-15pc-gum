"""Existing CAD models: downloaded to a local cache (never committed) and compared with my
parts, by size and by hole spacing. Their models come in millimeters and any orientation."""

import pytest

MM = 0.001


def board_mm(width_mm):
    """A made-up maker's model of a 35 x 35 board, in millimeters, standing on its edge."""
    from build123d import Box, Cylinder, Pos, Rot

    board = Box(width_mm, 35, 7.4)
    for x, y in ((15.25, 15.25), (-15.25, 15.25), (-15.25, -15.25), (15.25, -15.25)):
        board -= Pos(x, y, 0) * Cylinder(2, 20)
    return Rot(90, 0, 0) * board


def mine():
    from build123d import Align, Box, Cylinder, Pos

    board = Box(0.035, 0.035, 0.0074, align=(Align.CENTER, Align.CENTER, Align.MIN))
    for x, y in ((15.25, 15.25), (-15.25, 15.25), (-15.25, -15.25), (15.25, -15.25)):
        board -= Pos(x * MM, y * MM, 0) * Cylinder(0.002, 0.05)
    return board


def test_a_matching_model_matches():
    from pcs14.cad.existing import compare

    result = compare(mine(), board_mm(35).scale(MM), hole_diameter=0.004)
    assert result.size_ok
    assert result.holes_ok
    assert result.mine == pytest.approx(sorted([0.035, 0.035, 0.0074]))


def test_a_wider_model_gets_flagged():
    from pcs14.cad.existing import compare

    result = compare(mine(), board_mm(40).scale(MM), hole_diameter=0.004)
    assert not result.size_ok
    assert result.holes_ok  # same holes, different outline
    assert "40.0" in result.note


def test_hole_spacings_ignore_orientation():
    from pcs14.cad.existing import hole_spacings

    spacings = hole_spacings(board_mm(35).scale(MM), 0.004)
    assert spacings[:4] == pytest.approx([0.0305] * 4)
    assert spacings[4:] == pytest.approx([0.0305 * 2**0.5] * 2)


def test_an_empty_cache_is_just_not_downloaded(tmp_path):
    from pcs14.cad.existing import cached_model

    assert cached_model(tmp_path, "holybro-kakute-h7") is None


def test_loading_a_cached_step_comes_back_in_meters(tmp_path):
    from build123d import Box, export_step

    from pcs14.cad.existing import cached_model, load_model

    folder = tmp_path / "some-part"
    folder.mkdir()
    export_step(Box(35, 35, 7.4), folder / "model.step")  # written in millimeters
    path = cached_model(tmp_path, "some-part")
    assert path is not None
    size = load_model(path).bounding_box().size
    assert (size.X, size.Y, size.Z) == pytest.approx((0.035, 0.035, 0.0074))
