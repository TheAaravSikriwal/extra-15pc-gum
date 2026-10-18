"""The catalog's cad block: each part's shape, where its dimensions came from, which ones are
estimates, and whether a CAD model of it already exists."""

import shutil
from pathlib import Path

import pytest

from pcs14.catalog import CatalogError, SourceKind, load_catalog

FIXTURES = Path(__file__).parent / "fixtures" / "catalog"


@pytest.fixture
def scratch(tmp_path):
    copy = tmp_path / "catalog"
    shutil.copytree(FIXTURES, copy)
    return copy


def board(cad_lines: str, source: str = "{kind: made_up, note: test}") -> str:
    return f"""type: component
id: testco-board
maker: Testco
model: Board
source: {source}
mass_g: 8
cad:
{cad_lines}"""


GOOD = """  shape: board
  length_mm: 36
  width_mm: 36
  thickness_mm: 1.6
  top_mm: 5
  holes:
    - {x_mm: 15.25, y_mm: 15.25, diameter_mm: 4}
    - {x_mm: -15.25, y_mm: 15.25, diameter_mm: 4}
  source: {kind: made_up, note: test}
  estimates: [top_mm]
  estimate_note: guessed from a photo
  existing: {found: none, checked: 2026-10-17, note: looked on the maker's site}
"""


def load(folder: Path, text: str, **kwargs):
    (folder / "components" / "testco-board.yaml").write_text(text, encoding="utf-8")
    return load_catalog(folder, **kwargs)


def test_a_good_cad_block_loads_and_comes_out_metric(scratch):
    part = load(scratch, board(GOOD), allow_made_up=True).component("testco-board")
    assert part.cad.shape == "board"
    assert part.cad.size("length_mm") == pytest.approx(0.036)
    assert part.cad.holes[0].x == pytest.approx(0.01525)
    assert part.cad.estimates == ["top_mm"]
    assert part.cad.existing.found == "none"


def test_every_cad_block_says_whether_a_cad_model_already_exists(scratch):
    text = board(
        GOOD.replace(
            "  existing: {found: none, checked: 2026-10-17, note: looked on the maker's site}\n", ""
        )
    )
    with pytest.raises(CatalogError, match="existing"):
        load(scratch, text, allow_made_up=True)


def test_a_found_cad_model_needs_its_link_and_terms(scratch):
    text = board(GOOD.replace("found: none", "found: official"))
    with pytest.raises(CatalogError, match="link and its terms"):
        load(scratch, text, allow_made_up=True)


def test_estimates_have_to_name_real_dimensions(scratch):
    text = board(GOOD.replace("estimates: [top_mm]", "estimates: [hieght_mm]"))
    with pytest.raises(CatalogError, match="hieght_mm"):
        load(scratch, text, allow_made_up=True)


def test_estimates_need_a_note_saying_how(scratch):
    text = board(GOOD.replace("  estimate_note: guessed from a photo\n", ""))
    with pytest.raises(CatalogError, match="estimate_note"):
        load(scratch, text, allow_made_up=True)


def test_an_unknown_shape_fails_clearly(scratch):
    with pytest.raises(CatalogError, match="shape"):
        load(scratch, board(GOOD.replace("shape: board", "shape: blob")), allow_made_up=True)


def test_made_up_dimensions_cant_get_into_the_real_catalog(tmp_path):
    folder = tmp_path / "catalog"
    (folder / "components").mkdir(parents=True)
    real = "{kind: estimate, note: a real part with made-up dimensions}"
    with pytest.raises(CatalogError, match="made up"):
        load(folder, board(GOOD, source=real))


def test_weights_from_the_cad_are_their_own_kind_of_source(scratch):
    text = board(GOOD).replace(
        "source: {kind: made_up, note: test}\nmass_g", "source: {kind: cad}\nmass_g"
    )
    with pytest.raises(CatalogError, match="note"):
        load(scratch, text, allow_made_up=True)
    assert SourceKind("cad") is SourceKind.CAD


def test_a_thrust_table_cant_come_from_the_cad(scratch):
    motor = scratch / "motors" / "testco-m2810-900kv.yaml"
    text = motor.read_text(encoding="utf-8")
    first = text.index("    source:")
    end = text.index("\n", first)
    text = text[:first] + "    source: {kind: cad, note: nope}" + text[end:]
    motor.write_text(text, encoding="utf-8")
    with pytest.raises(CatalogError, match="thrust table"):
        load_catalog(scratch, allow_made_up=True)
