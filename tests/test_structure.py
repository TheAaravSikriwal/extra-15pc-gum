"""The structure side track's beam math, against hand-worked numbers."""

import math

import pytest

from pcs14.structure import beams

# a 7 x 15 mm carbon arm, 185 mm free, a 100 g motor and prop at its tip
ARM = beams.Arm(length_m=0.185, width_m=0.015, thickness_m=0.007, density_kg_m3=1600,
                tip_mass_kg=0.100)  # fmt: skip


def test_the_arm_bends_like_a_textbook_cantilever():
    # I = 15 x 7^3 / 12 = 428.75 mm^4; 21.6 N at 185 mm is 4.0 N m at the root
    assert ARM.second_moment() == pytest.approx(428.75e-12)
    assert ARM.root_stress(21.6) == pytest.approx(21.6 * 0.185 * 0.0035 / 428.75e-12)
    assert ARM.root_stress(21.6) / 1e6 == pytest.approx(32.6, abs=0.1)  # MPa
    # F L^3 / 3 E I, at 50 GPa: 2.1 mm
    assert ARM.tip_deflection(21.6, 50e9) * 1000 == pytest.approx(2.13, abs=0.01)


def test_its_first_modes_come_from_its_stiffness_and_tip_mass():
    k = 3 * 50e9 * 428.75e-12 / 0.185**3
    m = 0.100 + 0.24 * (1600 * 0.015 * 0.007 * 0.185)
    assert ARM.first_mode_hz(50e9) == pytest.approx(math.sqrt(k / m) / (2 * math.pi))
    assert ARM.first_mode_hz(50e9) == pytest.approx(48.8, abs=0.2)
    # in the frame's plane it's (15 / 7)^2 as stiff, so 15 / 7 as high in frequency
    ratio = ARM.first_mode_hz(50e9, vertical=False) / ARM.first_mode_hz(50e9)
    assert ratio == pytest.approx(15 / 7)


def test_a_prop_shakes_the_arm_once_a_turn_and_once_a_blade():
    turn, blade = beams.excitations_hz(600.0, blades=3)
    assert turn == pytest.approx(95.49, abs=0.01) and blade == pytest.approx(3 * turn)
    assert beams.crossing_rad_s(95.49) == pytest.approx(600.0, abs=0.1)


def test_a_joint_counts_only_some_of_its_fasteners():
    joint = beams.Joint("four screws", 4, (300.0, 400.0), "")
    assert joint.margin(200.0) == (3.0, 4.0)  # two of four carry it
    assert beams.screw_tension_n(5.03, 80) == pytest.approx(402.4)


def test_the_report_finds_the_mode_near_the_hover(tmp_path):
    import json
    from pathlib import Path

    from pcs14.catalog import load_catalog
    from pcs14.design import load_build
    from pcs14.structure import report

    design = Path(__file__).parent.parent / "design"
    build = load_build(design / "build.yaml", load_catalog(design / "catalog"))
    exports = tmp_path / "exports"
    for setup, hover in (("base", 554.0), ("max", 645.0)):
        folder = exports / "models" / f"pcs14_{setup}"
        folder.mkdir(parents=True)
        (folder / "model.json").write_text(
            json.dumps(
                {
                    "setup": setup,
                    "hover_rot_velocity": hover,
                    "top_rot_velocity": 947.0,
                    "mass_kg": 2.37,
                }
            )
        )
    (exports / "models" / "pcs14_payload").mkdir()  # the payload has no numbers
    docs = tmp_path / "docs"
    (docs / "reports" / "modules").mkdir(parents=True)
    (docs / "reports" / "modules" / "modules.json").write_text(
        json.dumps({"jolts": [{"bound_n": 254.0}, {"bound_n": 171.0}]})
    )
    written = report.write(build, docs, exports, tmp_path / "out", "2026-10-21")
    text = (tmp_path / "out" / "README.md").read_text(encoding="utf-8")
    data = json.loads((tmp_path / "out" / "structure.json").read_text(encoding="utf-8"))
    assert data["verdict"] == "open" and data["near"]  # the in-plane mode, near the hover
    assert "254 N" in text and len(written) == 4
