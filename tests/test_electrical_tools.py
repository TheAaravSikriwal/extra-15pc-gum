"""The electrical layer's foundations: the outside tools get found, and pcs14 electrical exists.

The tools aren't Python packages (Graphviz's dot for WireViz, ngspice, KiCad's command line),
so tests that need one skip cleanly when it isn't installed. CI installs them on Linux.
"""

import os
import subprocess
import sys

import pytest

from pcs14.cli import main
from pcs14.electrical import tools

EXE = ".exe" if sys.platform == "win32" else ""


def fake_program(folder, name, suffix=EXE):
    folder.mkdir(parents=True, exist_ok=True)
    path = folder / f"{name}{suffix}"
    path.write_text("")
    path.chmod(0o755)
    return path


def needs(key):
    return pytest.mark.skipif(tools.find(key) is None, reason=f"{key} isn't installed")


def test_the_environment_variable_wins(tmp_path):
    program = fake_program(tmp_path / "anywhere", "my-ngspice")
    on_path = fake_program(tmp_path / "bin", "ngspice")
    environ = {"PCS14_NGSPICE": str(program), "PATH": str(on_path.parent)}
    assert tools.find("ngspice", environ) == program


def test_then_the_path(tmp_path):
    program = fake_program(tmp_path / "bin", "dot")
    assert tools.find("dot", {"PATH": str(program.parent)}) == program


def test_ngspice_prefers_its_console_build(tmp_path):
    # on Windows, plain ngspice.exe opens a window; ngspice_con is the one for batch runs
    fake_program(tmp_path / "bin", "ngspice")
    console = fake_program(tmp_path / "bin", "ngspice_con")
    assert tools.find("ngspice", {"PATH": str(console.parent)}) == console


def test_then_where_the_installer_puts_it_newest_version_first(tmp_path):
    programs = tmp_path / "Programs" / "KiCad"
    # Windows installers lay it out like this, so it's .exe on any system
    fake_program(programs / "9.0" / "bin", "kicad-cli", ".exe")
    newest = fake_program(programs / "10.0" / "bin", "kicad-cli", ".exe")
    environ = {"PATH": str(tmp_path / "empty"), "LOCALAPPDATA": str(tmp_path)}
    found = tools.find("kicad-cli", environ, windows=True)
    assert found is not None and found.resolve() == newest.resolve()


def test_nothing_found_is_none(tmp_path):
    assert tools.find("kicad-cli", {"PATH": str(tmp_path)}, windows=True) is None


def test_a_variable_pointing_nowhere_is_ignored(tmp_path):
    program = fake_program(tmp_path / "bin", "dot")
    environ = {"PCS14_DOT": str(tmp_path / "gone.exe"), "PATH": str(program.parent)}
    assert tools.find("dot", environ) == program


def test_require_says_how_to_fix_it(tmp_path):
    with pytest.raises(tools.ToolMissing) as missing:
        tools.require("ngspice", {"PATH": str(tmp_path)})
    assert isinstance(missing.value, OSError)  # so the command line reports it cleanly
    assert "ngspice" in str(missing.value) and "PCS14_NGSPICE" in str(missing.value)


def test_the_command_lists_the_tools(capsys):
    assert main(["electrical", "--tools"]) == 0
    out = capsys.readouterr().out
    for name in ("Graphviz", "ngspice", "KiCad"):
        assert name in out


@needs("dot")
def test_wireviz_draws_a_harness():
    harness = {
        "connectors": {"A": {"pinlabels": ["5V", "GND"]}, "B": {"pinlabels": ["5V", "GND"]}},
        "cables": {"W1": {"wirecount": 2, "length": 0.1}},
        "connections": [[{"A": [1, 2]}, {"W1": [1, 2]}, {"B": [1, 2]}]],
    }
    assert "<svg" in tools.draw_harness(harness)


@needs("ngspice")
def test_ngspice_runs_a_circuit(tmp_path):
    circuit = tmp_path / "rc.cir"
    circuit.write_text(
        "rc\nV1 in 0 PULSE(0 3.3 1n 1n 1n 1u 2u)\nR1 in out 1k\nC1 out 0 1n\n.tran 1n 3u\n.end\n"
    )
    raw = tmp_path / "rc.raw"
    run = subprocess.run(
        [str(tools.require("ngspice")), "-b", "-r", str(raw), str(circuit)],
        capture_output=True,
        text=True,
        timeout=60,
    )
    assert run.returncode == 0, run.stdout + run.stderr
    assert raw.stat().st_size > 0


@pytest.mark.kicad
@needs("kicad-cli")
def test_kicad_answers():
    run = subprocess.run(
        [str(tools.require("kicad-cli")), "version"], capture_output=True, text=True, timeout=60
    )
    assert run.returncode == 0
    assert run.stdout.strip().split(".")[0] == "10"


def test_the_finder_never_touches_the_real_environment_by_accident(tmp_path):
    before = dict(os.environ)
    tools.find("dot", {"PATH": str(tmp_path)})
    assert dict(os.environ) == before
