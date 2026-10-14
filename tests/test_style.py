"""Checks on media/style.yaml, since every render and chart reads its colors from there."""

import re
from pathlib import Path

import yaml

STYLE = Path(__file__).resolve().parents[1] / "media" / "style.yaml"
HEX = re.compile(r"^#[0-9A-Fa-f]{6}$")


def load():
    return yaml.safe_load(STYLE.read_text(encoding="utf-8"))


def test_every_color_is_a_real_hex():
    style = load()
    colors = {**style["colors"], "pass": style["data"]["pass"], "fail": style["data"]["fail"]}
    for name, value in colors.items():
        assert HEX.match(value), f"{name} = {value!r}"


def test_pass_and_fail_look_different():
    data = load()["data"]
    assert data["pass"].lower() != data["fail"].lower()


def test_sizes_are_width_by_height():
    for name, (w, h) in load()["sizes"].items():
        assert w > 0 and h > 0, name
    assert load()["sizes"]["portrait"] == [1080, 1350]
