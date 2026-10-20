"""The CAD report and cad.json, from a small made-up run, plus the pcs14 cad command."""

import json
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]
GOLDEN = Path(__file__).parent / "fixtures" / "cad_report" / "README.md"


def made_up_run():
    from build123d import Box

    from pcs14.cad.checks import CombinationResult, Finding
    from pcs14.cad.mass import MassProperties
    from pcs14.cad.printed import PrintedPart
    from pcs14.cad.report import CadRun, Estimate, ExistingRow, HardwareRow, PieceRow

    inertia = ((0.016, 0.0, 0.0), (0.0, 0.019, 0.0), (0.0, 0.0, 0.026))
    passing = CombinationResult(
        setup="base",
        modules=frozenset(),
        trim_x=-0.011,
        overload=0.001,
        mass=MassProperties(1.776, (0.0001, 0.0, -0.0025), inertia),
        findings=(
            Finding("balance", True, 0.001, 0.05, "the busiest motor works 0.1% harder"),
            Finding("collisions", True, 0.0, 1e-9, "nothing overlaps"),
            Finding(
                "prop clearance",
                True,
                0.0106,
                0.010,
                "frame is 10.6 mm from prop 1's disk",
                ("prop disk 1", "frame"),
            ),
        ),
    )
    failing = CombinationResult(
        setup="mission",
        modules=frozenset({"V", "P"}),
        trim_x=-0.014,
        overload=0.062,
        mass=MassProperties(2.091, (0.0092, 0.0002, 0.012), inertia),
        findings=(
            Finding("balance", False, 0.062, 0.05, "the busiest motor works 6.2% harder"),
            Finding("collisions", True, 0.0, 1e-9, "nothing overlaps"),
            Finding(
                "compass distance",
                False,
                0.028,
                0.100,
                "the compass is 28 mm from the BEC",
                ("gps", "bec"),
            ),
        ),
    )
    printed = [
        PrintedPart(
            "module rail",
            ((Box(0.1, 0.03, 0.006), "petg_cf"),),
            "petg_cf",
            0.002,
            (0, 0, -1),
            "base",
            "module-mount",
            mass=0.0134,
        ),
        PrintedPart(
            "leg front left",
            ((Box(0.01, 0.01, 0.07), "tpu"),),
            "tpu",
            0.0019,
            (0, 0, 1),
            "base",
            "landing-legs",
            mass=0.0066,
        ),
    ]
    return CadRun(
        build_label="Testco M2810 / P10x4.5 / 6S2P",
        results=(passing, failing),
        printed=tuple(printed),
        catalog_masses={"module-mount": 0.030},
        wire_lengths={"battery leads": 0.1234, "receiver": 0.0471},
        estimates=(Estimate("testco-frame", ("arm_width_mm",), "traced from a render"),),
        existing=(
            ExistingRow("testco-fc", "official", "No license; don't commit", "holes line up"),
            ExistingRow("testco-gps", "none", None, None),
        ),
        exports=("outputs/cad/drone.step", "outputs/cad/drone.glb"),
        hardware=(HardwareRow("landing-legs", "M3 x 12 screw", 8, "steel", 1.034),),
        pieces=(
            PieceRow("frame", "frame", "base", 343.0, "testco-frame", False),
            PieceRow("prop front left", "prop", "base", 16.8, "testco-prop", True),
        ),
    )


@pytest.fixture(scope="module")
def run():
    return made_up_run()


def test_the_report_matches_a_known_good_copy(run):
    from pcs14.cad.report import render

    assert render(run, generated="2026-10-18") == GOLDEN.read_text(encoding="utf-8")


def test_the_data_file_matches_the_results(run):
    from pcs14.cad.report import to_data

    data = to_data(run, generated="2026-10-18")
    assert data["verdict"] == "fail"
    mission = next(c for c in data["combinations"] if c["setup"] == "mission")
    assert mission["trim_x_mm"] == pytest.approx(-14)
    assert mission["center_of_gravity_mm"] == pytest.approx([9.2, 0.2, 12.0])
    assert mission["mass_g"] == pytest.approx(2091)
    assert not mission["passed"]
    assert {f["check"] for f in mission["findings"] if not f["passed"]} == {
        "balance",
        "compass distance",
    }
    assert data["printed_parts"][0]["mass_g"] == pytest.approx(13.4)
    assert data["wire_lengths_mm"]["battery leads"] == pytest.approx(123.4)
    # every piece, named as the GLB names its node, for the project site's explorer
    prop = {"name": "prop front left", "kind": "prop", "module": "base", "mass_g": 16.8,
            "part_id": "testco-prop", "moving": True}  # fmt: skip
    assert data["pieces"][1] == prop
    json.dumps(data)  # it has to be plain JSON


def test_the_cad_command_writes_the_report(tmp_path, capsys):
    from pcs14.cli import main

    out = tmp_path / "report"
    args = ["cad", "--out", str(out), "--skip-exports", "--no-record"]
    assert main(args) == 0
    assert (out / "README.md").is_file()
    data = json.loads((out / "cad.json").read_text(encoding="utf-8"))
    assert len(data["combinations"]) == 8
    assert "combinations" in capsys.readouterr().out
