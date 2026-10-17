"""The pcs14 package ("14 pcs left") installs, imports and runs from the command line."""

import subprocess
import sys
from importlib.metadata import version

import pytest

import pcs14
from pcs14.cli import main


def test_version_comes_from_the_installed_package():
    assert pcs14.__version__ == version("pcs14")


def test_version_flag_prints_the_name_and_version(capsys):
    with pytest.raises(SystemExit) as exit_info:
        main(["--version"])
    assert exit_info.value.code == 0
    assert capsys.readouterr().out.strip() == f"pcs14 {pcs14.__version__}"


def test_no_arguments_prints_help_without_failing(capsys):
    assert main([]) == 0
    assert "14 pcs left" in capsys.readouterr().out


def test_runs_as_a_module():
    result = subprocess.run(
        [sys.executable, "-m", "pcs14", "--version"],
        capture_output=True,
        text=True,
        check=True,
    )
    assert result.stdout.strip() == f"pcs14 {pcs14.__version__}"
