"""The firmware guide: PX4 first on the ARK FPV, then my firmware, then the safety monitor,
and what isn't built yet. Each combination's PX4 parameters (the flight sim's, less the
simulator's own) and my firmware's airframe file are copied beside it.
"""

import json
from pathlib import Path

PX4_VERSION = "v1.17.0"  # what the flight sim flies (pcs14.flight.report)
PX4_TARGET = "ark_fpv_default"  # boards/ark/fpv in PX4's tree
SIM_ONLY = ("SIM_",)  # parameters only the simulator reads


def px4_params(params: dict) -> dict:
    """The flight sim's parameters a real ARK FPV takes: everything but the simulator's."""
    return {k: v for k, v in sorted(params.items()) if not k.startswith(SIM_ONLY)}


def params_text(setup: str, params: dict) -> str:
    lines = [
        f"# PX4 {PX4_VERSION} parameters for {setup}, from the flight sim (pcs14 flight-sim)",
        "# Paste into the MAVLink console (QGroundControl, Analyze Tools), then reboot.",
        "# The motors' outputs and DShot are set in QGroundControl's Actuators page.",
    ]
    for name, value in px4_params(params).items():
        text = f"{value:g}" if isinstance(value, float) else str(value)
        lines.append(f"param set {name} {text}")
    return "\n".join(lines) + "\n"


def write_setup_files(exports, out) -> list[Path]:
    """Each combination's PX4 parameters and my firmware's airframe file, from the flight
    sim's generated models, into out/firmware/."""
    written = []
    folder = Path(out) / "firmware"
    for model in sorted(Path(exports, "models").glob("pcs14_*")):
        params, airframe = model / "params.json", model / "firmware.txt"
        if not params.is_file():
            continue
        setup = json.loads((model / "model.json").read_text(encoding="utf-8"))["setup"]
        folder.mkdir(parents=True, exist_ok=True)
        path = folder / f"px4-{model.name}.txt"
        path.write_text(params_text(setup, json.loads(params.read_text("utf-8"))), "utf-8")
        written.append(path)
        if airframe.is_file():
            copy = folder / f"airframe-{model.name}.txt"
            copy.write_text(airframe.read_text("utf-8"), "utf-8")
            written.append(copy)
    return written


def render(build, files: list[Path], generated: str) -> str:
    cell = build.pack.cell
    px4_files = [f for f in files if f.name.startswith("px4-")]
    out = [
        "# The firmware",
        "",
        f"*Generated {generated} by `pcs14 package`. PX4 flies first: the ARK FPV runs it out "
        "of the box, the flight sim tuned it for this drone, and nothing of mine has flown a "
        "real motor yet.*",
        "",
        "## 1. PX4 on the ARK FPV",
        "",
        f"PX4 {PX4_VERSION}, the version the flight sim flies. The ARK FPV is in PX4's tree as "
        f"`boards/ark/fpv`, so the build target is `{PX4_TARGET}`:",
        "",
        "```bash",
        f"git clone --branch {PX4_VERSION} --recursive https://github.com/PX4/PX4-Autopilot.git",
        "```",
        "",
        "```bash",
        f"make -C PX4-Autopilot {PX4_TARGET} upload",
        "```",
        "",
        "Or load the same release from QGroundControl's firmware page. Then, in QGroundControl:",
        "",
        "- the airframe: Generic Quadcopter (4001), then this combination's parameters below, "
        "pasted into the MAVLink console, and a reboot;",
        "- the Actuators page: motors 1 to 4 on the ESC's outputs, DShot600, and each motor's "
        "direction checked with the props off (motor 1 front right, 2 back left, 3 front left, "
        "4 back right, PX4's quad X);",
        "- the sensors' calibration (the compass on the GPS mast, the accelerometer, the "
        "level), the radio, and the flight modes, with the kill switch on its own switch;",
        f"- the battery: {build.pack.series} cells, "
        f"{round(cell.capacity_mah * build.pack.parallel)} mAh. "
        "PX4's battery defaults are for LiPo; these are Li-ion cells, "
        f"{cell.maker} {cell.model}, which go down to {cell.min_voltage_v:g} V a cell, so set "
        "the empty voltage near 3.0 V a cell and check the percentage against a real "
        "discharge before trusting it.",
        "",
        "The parameters, one file a combination (the flight sim's, less its simulator's own):",
        "",
    ]
    out += [f"- [{f.name}](firmware/{f.name})" for f in px4_files]
    if not px4_files:
        out += ["- none yet: run `pcs14 flight-sim` first, which generates them"]
    out += [
        "",
        "## 2. My firmware",
        "",
        "C++17, in `firmware/`. The core and every driver's logic build and test on any machine:",
        "",
        "```bash",
        "cmake -S firmware -B build/firmware",
        "```",
        "",
        "```bash",
        "cmake --build build/firmware",
        "```",
        "",
        "```bash",
        "ctest --test-dir build/firmware",
        "```",
        "",
        "The ARK FPV's image needs the ARM compiler (in WSL: `sudo apt install "
        "gcc-arm-none-eabi libnewlib-arm-none-eabi libstdc++-arm-none-eabi-newlib`), and CI "
        "builds it on every push:",
        "",
        "```bash",
        "cmake -S firmware -B build/h743 -DCMAKE_BUILD_TYPE=Release "
        "-DCMAKE_TOOLCHAIN_FILE=firmware/cmake/arm-none-eabi.cmake",
        "```",
        "",
        "```bash",
        "cmake --build build/h743 --target pcs14_h743",
        "```",
        "",
        "**It isn't ready to fly.** The image builds, but its register-level drivers (the "
        "IMU's SPI, the DShot timers, the SD card's SDMMC) have only run against the host "
        "tests, never on a board. They wait for a bench ARK FPV, props off, checked one at a "
        "time against PX4 on the same board. Each combination's airframe file, which my "
        "firmware reads for its mass, inertia, rotors and motors, is in `firmware/` beside "
        "PX4's parameters. Self-tuning (step 7) found the inertia within 0.3% in the sim; on "
        "the drone it runs from a log of three stick doublets, on the ground.",
        "",
        "## 3. The safety monitor",
        "",
        "The Teensy 4.1's core logic is in `firmware/monitor/`, tested on the host and flown "
        "in the sim beside my firmware. **Its image for the Teensy isn't built yet:** that "
        "needs PJRC's Teensy core for the i.MX RT1062 (or a startup of my own), which is a "
        "download I haven't made. Until it's built and has passed its bench tests, the "
        "safety monitor isn't on the drone, and the kill switch works through the flight "
        "controller alone. The first flights are PX4's, tethered, with that in mind.",
        "",
    ]
    return "\n".join(out)
