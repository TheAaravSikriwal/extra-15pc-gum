"""The project site's colors are the project's (media/style.yaml): its CSS variables can't
drift from the file every chart and still reads."""

import re
from pathlib import Path

import yaml

ROOT = Path(__file__).resolve().parents[1]


def test_the_sites_colors_are_the_style_files():
    style = yaml.safe_load((ROOT / "media" / "style.yaml").read_text(encoding="utf-8"))
    css = (ROOT / "site" / "src" / "style" / "tokens.css").read_text(encoding="utf-8")
    found = {k: v.lower() for k, v in re.findall(r"--([a-z-]+):\s*(#[0-9a-fA-F]{6})", css)}
    for name, color in style["colors"].items():
        assert found.get(name) == color.lower(), name
    for name in ("pass", "fail"):
        assert found.get(name) == style["data"][name].lower(), name


def test_the_sites_fonts_are_the_style_files():
    style = yaml.safe_load((ROOT / "media" / "style.yaml").read_text(encoding="utf-8"))
    css = (ROOT / "site" / "src" / "style" / "tokens.css").read_text(encoding="utf-8")
    for role, font in style["fonts"].items():
        assert font in css, role
