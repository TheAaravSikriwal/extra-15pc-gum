"""The build package's assembly guide, on the real build: every part lands in a step, and every
screw lands with the part it holds."""

from pathlib import Path

import pytest

from pcs14.cad.settings import load_settings
from pcs14.catalog import load_catalog
from pcs14.design import load_build
from pcs14.package import assembly

ROOT = Path(__file__).parent.parent


@pytest.fixture(scope="module")
def build():
    return load_build(ROOT / "design" / "build.yaml", load_catalog(ROOT / "design" / "catalog"))


@pytest.fixture(scope="module")
def settings():
    return load_settings(ROOT / "design" / "cad.yaml")


def test_every_part_in_the_build_has_a_step(build):
    _, missing = assembly.covered(build)
    assert missing == set()


def test_every_screw_lands_with_the_part_it_holds_once(build, settings):
    for f in settings.hardware:
        steps = [s for s in assembly.STEPS if assembly.step_hardware(s, [f])]
        assert len(steps) == 1, f"{f.what} for {f.holds} is in {len(steps)} steps"


def test_the_guide_walks_every_step_in_order(settings):
    text = assembly.render(settings.hardware, "2026-10-21")
    at = [text.index(f"## {k}. {s.title}") for k, s in enumerate(assembly.STEPS, start=1)]
    assert at == sorted(at)
    assert "4 x M3 x 30 screw, steel: the stack" in text
