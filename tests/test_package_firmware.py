"""The build package's firmware guide: PX4's parameters from the flight sim, less the
simulator's own, and a guide that says what isn't built."""

import json
from pathlib import Path

from pcs14.catalog import load_catalog
from pcs14.design import load_build
from pcs14.package import firmware

ROOT = Path(__file__).parent.parent


def test_the_simulators_own_parameters_stay_behind():
    params = {"MC_ROLL_P": 9.0, "SIM_GZ_EC_MAX1": 947, "BAT1_N_CELLS": 6}
    assert firmware.px4_params(params) == {"BAT1_N_CELLS": 6, "MC_ROLL_P": 9.0}
    text = firmware.params_text("base", params)
    assert "param set MC_ROLL_P 9" in text and "SIM_" not in text.split("\n", 3)[3]


def test_each_combination_gets_its_parameters_and_airframe(tmp_path):
    model = tmp_path / "models" / "pcs14_v"
    model.mkdir(parents=True)
    (model / "model.json").write_text(json.dumps({"setup": "V"}))
    (model / "params.json").write_text(json.dumps({"MC_ROLL_P": 9.0, "SIM_GZ_EC_MAX1": 947}))
    (model / "firmware.txt").write_text("mass_kg 2.0\n")
    files = firmware.write_setup_files(tmp_path, tmp_path / "out")
    assert sorted(f.name for f in files) == ["airframe-pcs14_v.txt", "px4-pcs14_v.txt"]


def test_the_guide_puts_px4_first_and_names_what_isnt_built(tmp_path):
    build = load_build(ROOT / "design" / "build.yaml", load_catalog(ROOT / "design" / "catalog"))
    text = firmware.render(build, [], "2026-10-21")
    assert text.index("PX4 on the ARK FPV") < text.index("My firmware")
    assert "make -C PX4-Autopilot ark_fpv_default upload" in text
    assert "It isn't ready to fly" in text and "isn't built yet" in text
