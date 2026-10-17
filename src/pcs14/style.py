"""The project's look, read from media/style.yaml so every chart and view matches."""

from functools import cache
from pathlib import Path

import yaml

STYLE_FILE = Path(__file__).resolve().parents[2] / "media" / "style.yaml"

# The same values as media/style.yaml, for when the package runs outside the repo.
FALLBACK = {
    "colors": {
        "background": "#0B0B0B",
        "text": "#F4F4F2",
        "accent": "#3DDC97",
        "pop": "#E64FA0",
        "muted": "#B4B2A9",
        "lines": "#2C2C2A",
    },
    "data": {"field_colormap": "turbo", "pass": "#3DDC97", "fail": "#E64FA0"},
    "fonts": {"headline": "Space Grotesk", "body": "Inter", "numbers": "JetBrains Mono"},
    "sizes": {
        "portrait": [1080, 1350],
        "square": [1080, 1080],
        "vertical": [1080, 1920],
        "wide": [1920, 1080],
    },
}


@cache
def load() -> dict:
    if STYLE_FILE.is_file():
        return yaml.safe_load(STYLE_FILE.read_text(encoding="utf-8"))
    return FALLBACK


def color(name: str) -> str:
    return load()["colors"][name]


def rgb(name: str) -> tuple[int, int, int]:
    return hex_to_rgb(color(name))


def hex_to_rgb(value: str) -> tuple[int, int, int]:
    value = value.lstrip("#")
    return int(value[0:2], 16), int(value[2:4], 16), int(value[4:6], 16)


def verdict_color(verdict: str) -> str:
    """Spearmint for pass, magenta for fail, the muted gray for marginal."""
    data = load()["data"]
    return {"pass": data["pass"], "fail": data["fail"], "marginal": color("muted")}[verdict]
