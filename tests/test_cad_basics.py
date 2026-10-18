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


def test_the_cad_command_runs(capsys):
    assert main(["cad", *TEST_PARTS, "--no-record"]) == 0
    assert "parts" in capsys.readouterr().out
