"""The outside programs the electrical layer calls: Graphviz's dot (WireViz draws with it),
ngspice, and KiCad's command line.

None of them is a Python package, so each one gets looked for in the same order: an
environment variable naming the program, then the PATH, then where its Windows installer puts
it (newest version first). Anything that needs a missing tool raises ToolMissing, which says
how to fix it, and the tests that need one skip.
"""

import glob
import os
import re
import shutil
import sys
from collections.abc import Mapping
from contextlib import contextmanager
from dataclasses import dataclass
from pathlib import Path


@dataclass(frozen=True)
class Tool:
    name: str  # what people call it
    env: str  # an environment variable that can name the program
    commands: tuple[str, ...]  # names to look for on the PATH, in order
    places: tuple[str, ...]  # where Windows installers put it, with %VARIABLES% and globs
    install: str  # how to get it


TOOLS = {
    "dot": Tool(
        name="Graphviz",
        env="PCS14_DOT",
        commands=("dot",),
        places=("%ProgramFiles%/Graphviz/bin/dot.exe",),
        install="winget install Graphviz.Graphviz, or apt install graphviz",
    ),
    "ngspice": Tool(
        name="ngspice",
        env="PCS14_NGSPICE",
        # on Windows plain ngspice.exe opens a window; ngspice_con is the batch build
        commands=("ngspice_con", "ngspice"),
        places=(
            "%LOCALAPPDATA%/Programs/ngspice/bin/ngspice_con.exe",
            "%ProgramFiles%/ngspice/bin/ngspice_con.exe",
        ),
        install=(
            "unpack ngspice-47_64.7z from ngspice.sourceforge.io into "
            "%LOCALAPPDATA%\\Programs\\ngspice, or apt install ngspice"
        ),
    ),
    "kicad-cli": Tool(
        name="KiCad",
        env="PCS14_KICAD_CLI",
        commands=("kicad-cli",),
        places=(
            "%LOCALAPPDATA%/Programs/KiCad/*/bin/kicad-cli.exe",
            "%ProgramFiles%/KiCad/*/bin/kicad-cli.exe",
        ),
        install="winget install KiCad.KiCad, or KiCad 10 from ppa:kicad/kicad-10.0-releases",
    ),
}


class ToolMissing(OSError):
    pass


def find(
    key: str, environ: Mapping[str, str] | None = None, windows: bool | None = None
) -> Path | None:
    """Where the tool is, or None."""
    tool = TOOLS[key]
    environ = os.environ if environ is None else environ
    windows = sys.platform == "win32" if windows is None else windows

    named = environ.get(tool.env)
    if named and Path(named).is_file():
        return Path(named)
    for command in tool.commands:
        found = shutil.which(command, path=environ.get("PATH", ""))
        if found:
            return Path(found)
    if windows:
        for place in tool.places:
            pattern = _expand(place, environ)
            if pattern is None:
                continue
            matches = [Path(m) for m in glob.glob(pattern) if Path(m).is_file()]
            if matches:
                return max(matches, key=_version)
    return None


def require(key: str, environ: Mapping[str, str] | None = None) -> Path:
    found = find(key, environ)
    if found is None:
        tool = TOOLS[key]
        raise ToolMissing(
            f"{tool.name} isn't installed, or isn't where pcs14 looks. "
            f"Install it ({tool.install}), or set {tool.env} to the program's path."
        )
    return found


def describe() -> list[str]:
    """One line per tool: where it is, or how to get it."""
    lines = []
    for key, tool in TOOLS.items():
        found = find(key)
        where = str(found) if found else f"not found. Install it: {tool.install}"
        lines.append(f"{tool.name} ({key}): {where}")
    return lines


def draw_harness(harness: dict) -> str:
    """A WireViz harness as SVG. WireViz runs Graphviz's dot from the PATH, so dot's folder
    goes on the front of it for the call."""
    from wireviz.wireviz import parse

    with _on_path(require("dot").parent):
        return parse(harness, return_types="svg")


@contextmanager
def _on_path(folder: Path):
    before = os.environ.get("PATH", "")
    os.environ["PATH"] = str(folder) + os.pathsep + before
    try:
        yield
    finally:
        os.environ["PATH"] = before


def _expand(place: str, environ: Mapping[str, str]) -> str | None:
    """%NAME% replaced from the environment, or None if a variable isn't set."""
    names = re.findall(r"%([^%]+)%", place)
    lookup = {k.upper(): v for k, v in environ.items()}
    if any(name.upper() not in lookup for name in names):
        return None
    return re.sub(r"%([^%]+)%", lambda m: lookup[m.group(1).upper()], place)


def _version(path: Path) -> tuple[int, ...]:
    return tuple(int(n) for n in re.findall(r"\d+", str(path)))
