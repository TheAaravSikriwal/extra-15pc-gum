"""The CAD layer's foundations: build123d works, and the pcs14 cad command exists."""

from pathlib import Path

import pytest

from pcs14.cli import main

ROOT = Path(__file__).resolve().parents[1]
FIXTURES = Path(__file__).parent / "fixtures"
TEST_PARTS = [
    "--catalog",
    str(FIXTURES / "catalog"),
    "--build",
    str(FIXTURES / "build.yaml"),
    "--targets",
    str(ROOT / "design" / "targets.yaml"),
    "--allow-made-up",
]


def test_build123d_makes_solids():
    from build123d import Box

    assert Box(10, 10, 10).volume == pytest.approx(1000)


def test_the_cad_command_says_clearly_when_parts_cant_be_modeled(capsys):
    # the made-up test parts have no cad blocks
    assert main(["cad", *TEST_PARTS, "--no-record", "--skip-exports"]) == 2
    assert "no cad block" in capsys.readouterr().err
