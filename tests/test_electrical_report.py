"""The electrical report and electrical.json, from a small made-up run, plus its stills."""

import json
from pathlib import Path
from types import SimpleNamespace

import numpy as np
import pytest

from pcs14.electrical.checks import Finding
from pcs14.unproven import Unproven

GOLDEN = Path(__file__).parent / "fixtures" / "electrical_report" / "README.md"


def made_up_run(**changes):
    from dataclasses import replace

    from pcs14.electrical.report import CaseRow, ElectricalRun, Estimate, HeatRow, SwitchRow

    findings = (
        Finding("wire current", "pack.XT60.+ to reg.J.VIN", True, 2.1, 22.0, "A", "P, burst",
                "2.10 A in 18 AWG silicone, which carries 27.5 A to its 200 C limit"),
        Finding("wire current", "reg.J.VOUT to load.J.5V", True, 0.9, 22.0, "A", "base, hover",
                "0.90 A in 18 AWG silicone, which carries 27.5 A to its 200 C limit"),
        Finding("load voltage", "load.J.5V", False, 4.62, 4.75, "V", "P, worst",
                "4.620 to 4.700 V across the cases, inside 4.75 to 5.15 V",
                ("t-load: draws[J.5V]",)),
        Finding("connector burst", "pack.XT60.+", True, 91.0, 100.0, "C", "P, burst",
                "40 A for 10 s ends 51 K over the air"),
    )  # fmt: skip
    cases = (
        CaseRow("base", "hover", 22.1, 12.0),
        CaseRow("base", "cruise", 21.9, 14.5),
        CaseRow("base", "burst", 19.8, 40.0),
        CaseRow("base", "worst", 22.1, 12.0),
        CaseRow("P", "hover", 22.0, 12.6),
        CaseRow("P", "cruise", 21.8, 15.1),
        CaseRow("P", "burst", 19.7, 40.0),
        CaseRow("P", "worst", 22.0, 12.6),
    )
    switch = (
        SwitchRow("Teensy off", "The flight controller drives the ESC through the switch", True,
                  True, (1046, 1046), (1232, 1232), ("frames decode: the ESC decoded [1046]",)),
        SwitchRow("No buffers", "A dead Teensy straight on the line. Meant to fail", False, False,
                  (None, None), (None,), ("frames decode: the ESC decoded [None, None]",)),
    )  # fmt: skip
    shares = {
        ("base", "hover"): {"main": 0.12, "signal": 0.0},
        ("base", "burst"): {"main": 0.31, "signal": 0.0},
        ("P", "hover"): {"main": 0.13, "signal": 0.004},
        ("P", "burst"): {"main": 0.33, "signal": 0.004},
    }
    run = ElectricalRun(
        build_label="Testco M2810 / P10x4.5 / 6S2P",
        boards=3,
        wires=7,
        safety_paths=1,
        combinations=("base", "P"),
        problems=(),
        cases=cases,
        findings=findings,
        heat=(
            HeatRow("pack.XT60.+", 61.0, 91.0, 100.0),
            HeatRow("pack.XT60.+ to reg.J.VIN", 48.2, 60.1, 180.0),
        ),
        switch=switch,
        route_shares=shares,
        wire_amps={key: {"pack.XT60.+ to reg.J.VIN": 1.234567} for key in shares},
        power_tree="- pack.XT60.+\n  - reg.5V, a switching 5 V supply rated 3 A",
        pin_maps=(("mcu", "t-mcu", "| Pin | What it is | Called | Goes to |\n|---|---|---|---|"),),
        board_pins={
            "reg": {
                "part": "made-up-reg",
                "module": "base",
                "pins": [
                    {
                        "pin": "J.VIN",
                        "role": "power",
                        "functions": "",
                        "to": "pack.XT60.+",
                        "harness": "main",
                    }
                ],
            }
        },  # fmt: skip
        estimates=(
            Estimate("t-load", ("load",), ("draws[J.5V]",), "From a similar board."),
            Estimate("t-servo", ("servo",), (), "A stand-in until the real one is picked."),
        ),
        unproven=(Unproven(what="A dead short in the battery leads.", measure="Look."),),
        files=(
            "harnesses/power.svg",
            "kicad/electrical.kicad_sch",
            "stills/burst-heat.png",
            "stills/takeover-portrait.png",
            "stills/wire-work.png",
        ),
        erc=0,
        skipped=(),
        harnesses=("harnesses/power.svg",),
        exports=("outputs/electrical/electrical.svg",),
        routes={"main": ("pack.XT60.+ to reg.J.VIN",)},
    )
    return replace(run, **changes)


@pytest.fixture(scope="module")
def run():
    return made_up_run()


def test_the_report_matches_a_known_good_copy(run):
    from pcs14.electrical.report import render

    assert render(run, generated="2026-10-19") == GOLDEN.read_text(encoding="utf-8")


def test_the_data_file_matches_the_results(run):
    from pcs14.electrical.report import to_data

    data = to_data(run, generated="2026-10-19")
    assert data["verdict"] == "fail"
    failing = [f for f in data["findings"] if not f["passed"]]
    assert [(f["check"], f["subject"]) for f in failing] == [("load voltage", "load.J.5V")]
    assert failing[0]["rests_on"] == ["t-load: draws[J.5V]"]
    assert data["route_heating_share"]["P"]["burst"]["main"] == pytest.approx(0.33)
    assert data["wire_amps"]["base"]["hover"]["pack.XT60.+ to reg.J.VIN"] == 1.2346
    assert data["switch_sims"][1]["esc_frames"] == [None, None]
    assert data["kicad_rules_violations"] == 0
    # which wires run along each CAD route, so a route in 3D can name its wires' ends
    assert data["routes"] == {"main": ["pack.XT60.+ to reg.J.VIN"]}
    # every board's pins, for the project site's wiring page
    assert data["boards"]["reg"]["part"] == "made-up-reg"
    assert data["boards"]["reg"]["pins"][0]["to"] == "pack.XT60.+"
    json.dumps(data)  # it has to be plain JSON


def test_numbers_from_numpy_come_out_plain():
    from pcs14.electrical.report import to_data

    finding = Finding("x", "y", np.bool_(True), np.float64(1.5), 2.0, "A", "base, hover", "z")
    data = to_data(made_up_run(findings=(finding,)))
    assert data["findings"][0]["passed"] is True and type(data["findings"][0]["value"]) is float


def test_a_switch_sim_that_misbehaves_fails_the_verdict(run):
    from dataclasses import replace

    clean = made_up_run(findings=tuple(f for f in run.findings if f.passed))
    assert clean.passed
    flipped = replace(clean.switch[1], passed=True)  # meant to fail, but passed
    assert not made_up_run(findings=clean.findings, switch=(clean.switch[0], flipped)).passed


def _takeover_sim():
    t = np.linspace(0, 360e-6, 36001)
    bit = np.sign(np.sin(t * 2 * np.pi * 600e3)) * 1.65 + 1.65
    ctl = np.where(t > 110e-6, 3.3, 0.0)
    return SimpleNamespace(
        waves={"time": t, "v(fc)": bit, "v(esc)": np.where(t > 110e-6, 3.3, bit), "v(ctl)": ctl},
        esc_frames=[1046, None, 0, 0],
    )


def test_the_stills_come_in_the_post_sizes(tmp_path):
    from PIL import Image

    from pcs14 import style
    from pcs14.electrical import stills

    for size in stills.SIZES:
        path = stills.takeover(_takeover_sim(), tmp_path / f"t-{size}.png", size)
        assert Image.open(path).size == tuple(style.load()["sizes"][size])
    curves = [
        ("pack.XT60.+", [(0.0, 77.0), (10.0, 128.0)], 100.0),
        ("pack.XT60.-", [(0.0, 77.0), (10.0, 128.0)], 100.0),
        ("lead.XT60.+ to esc.BAT.VBAT", [(0.0, 61.0), (10.0, 80.0)], 180.0),
    ]
    heat = stills.burst_heat(curves, tmp_path / "heat.png", air_c=40)
    shares = {("max", "burst"): {"battery leads": 0.29, "receiver": 0.0}}
    work = stills.wire_work(shares, {("max", "burst"): {"pack.XT60.+": 1.47}}, tmp_path / "w.png")
    for path in (heat, work):
        assert Image.open(path).size == tuple(style.load()["sizes"]["portrait"])


def test_the_tightest_temperature_is_the_one_using_most_of_its_rise():
    from pcs14.electrical.report import render

    cold = Finding("wire temperature", "thin feed", True, 40.0, 60.0, "C", "max, hover", "cold")
    warm = Finding("wire temperature", "battery lead", True, 61.0, 160.0, "C", "max, hover", "warm")
    text = render(made_up_run(findings=(cold, warm)))
    # the thin feed sits at the air's 40 C, so the lead (21 of its 120 K) is the tighter one
    assert "| wire temperature | 2 | 2 | battery lead, max, hover: warm |" in text
