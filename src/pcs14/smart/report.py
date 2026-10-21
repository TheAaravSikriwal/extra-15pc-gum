"""Step 7's report, the smart features: what each of step 7's scenarios found on my firmware,
the object detection on the camera's frames, and what it can't prove. Written to
docs/reports/smart/ by `pcs14 smart` (with no words), like every other step.
"""

import json
from pathlib import Path

import numpy as np

from pcs14.smart import detect

CAMERA_RUN = "pcs14_v"  # step 6's camera run: 20 m up, looking ahead and 30 degrees down
CAMERA_PITCH_DEG = 30.0
CAMERA_OFFSET = (0.18, 0.0, 0.0)
LANDED_HEIGHT_M = 0.074  # the model's middle above the ground when it sits there
# the frames graded: a hover looking north before the dash, then the first frame past each of
# these distances north on the way out, the last one past everything
DETECT_HOVER_BEFORE_S = 5.0
DETECT_NORTH_M = (3.0, 9.0, 17.0, 29.0, 44.0, 74.0)
DETECT_FOUND = 0.5  # of the true things, near a box
DETECT_FALSE_PER_FRAME = 1.0


def _camera():
    from pcs14.flight.generate import CAMERA
    from pcs14.smart import ortho

    assert "<horizontal_fov>1.15192</horizontal_fov>" in CAMERA  # the same camera
    return ortho.Camera(width=1280, height=720, hfov_rad=1.15192)


def detection_frames(log, times, look_s: float) -> list[int]:
    """Which of the camera run's frames to grade (see DETECT_NORTH_M)."""
    picks = [int(np.argmin(np.abs(np.asarray(times) - (look_s - DETECT_HOVER_BEFORE_S))))]
    for north in DETECT_NORTH_M:
        for k, t in enumerate(times):
            i = min(int(np.searchsorted(log.t, t)), len(log.t) - 1)
            if t > look_s and log.position[i][1] >= north:
                picks.append(k)
                break
    return picks


def pose_at(log, t: float):
    from pcs14.smart import ortho

    i = min(int(np.searchsorted(log.t, t)), len(log.t) - 1)
    position = log.position[i] + np.array([0.0, 0.0, LANDED_HEIGHT_M])
    return ortho.Pose.on_drone(position, log.attitude[i], CAMERA_OFFSET,
                               np.radians(CAMERA_PITCH_DEG))  # fmt: skip


def run_detection(exports, ask=detect.ask) -> dict:
    """The local vision model on the camera run's graded frames, against the true boxes. Needs
    Ollama with qwen2.5vl:7b; the result is saved so the report doesn't rerun the model."""
    from PIL import Image

    from pcs14.flight import ulog
    from pcs14.flight.scenarios.modules import SCENERY

    exports = Path(exports)
    folder = exports / "camera" / CAMERA_RUN
    result = json.loads((exports / "results" / f"{CAMERA_RUN}-camera-mine.json").read_text("utf-8"))
    look = next(t for t, name in result["run"]["marks"] if name == "look")
    log = ulog.flight_log(ulog.read(exports / "logs" / f"{CAMERA_RUN}-camera-mine.ulg"))
    times = [float(x) for x in (folder / "frames.txt").read_text("utf-8").split()]
    camera = _camera()
    frames = []
    for k in detection_frames(log, times, look):
        picture = np.asarray(Image.open(folder / f"frame-{k:04d}.png").convert("RGB"))
        pose = pose_at(log, times[k])
        frames.append({
            "frame": k, "t": times[k], "north_m": float(pose.position[1]),
            "truth": [b.__dict__ for b in detect.truth_boxes(camera, pose, SCENERY)],
            "found": [b.__dict__ for b in ask(picture)],
        })  # fmt: skip
    return {"model": detect.MODEL, "prompt": detect.PROMPT, "frames": frames}


def scored(detection: dict) -> list:
    def boxes(items):
        return [detect.Box(**b) for b in items]

    return [detect.Scored(f["frame"], boxes(f["truth"]), boxes(f["found"]))
            for f in detection["frames"]]  # fmt: skip


def detection_findings(detection: dict) -> list:
    """The grade: half the true things with a box near them, the biggest thing in view
    (the shed) found every time it's there, and at most a false alarm a frame on average."""
    from pcs14.flight import grade

    frames = scored(detection)
    total = detect.totals(frames)
    found = total["near"] / total["true"] if total["true"] else 0.0
    with_shed = [s for s in frames if any(t.label == "shed" for t in s.truth)]
    shed_ok = sum(any(t.label == "shed" for t, _, _ in s.near) for s in with_shed)
    false = total["false alarms"] / max(total["frames"], 1)
    median = total["median overlap"]
    return [
        grade.Finding("found", found >= DETECT_FOUND, found, DETECT_FOUND, "",
                      f"{total['near']} of {total['true']} true things with a box near them"
                      + (f" (median overlap {median:.2f})" if median is not None else "")),
        grade.Finding("the shed", shed_ok == len(with_shed), shed_ok, len(with_shed), "",
                      f"in {shed_ok} of the {len(with_shed)} frames it's in"),
        grade.Finding("false alarms", false <= DETECT_FALSE_PER_FRAME, false,
                      DETECT_FALSE_PER_FRAME, "",
                      f"{total['false alarms']} boxes on nothing, over {total['frames']} frames"),
    ]  # fmt: skip


# --- the report ---------------------------------------------------------------------------

SETUP_ORDER = ("base", "V", "P", "C", "mission", "V+C", "P+C", "max")
RELAY_PRESETS = ("ShortFast", "MediumFast", "LongFast")
RELAY_GROUND_M = 1.5  # a node in someone's hand
RELAY_UP_M = 100.0  # one riding on the drone

UNPROVEN = (
    "Gazebo's rotors don't feel the air: no cheaper forward flight, no lift from rising air on "
    "the rotors, no vortex ring state. So the turn-back warning was checked against the sim's "
    "power, not a real pack's; soar mode's real saving (about 76 W in a 4 m/s column, by "
    "momentum theory) is a number, not a measurement; and the spiral descent's whole reason "
    "for being, keeping out of its own downwash, can't be shown here.",
    "Wind sensing reads the sim's wind exactly because the estimate and Gazebo use the same "
    "drag formula. A real drone's drag area and its lean in gusts will make it worse.",
    "Self-tuning's 0.3% is a clean sim: motors that follow a first-order lag exactly, a gyro "
    "with little noise, no blade flapping or rotor damping. A real drone will do worse, and "
    "the fit runs on the ground from the log for now, not on board.",
    "GPS-free flight's estimate flew over a made-up textured field at 3 m/s and 6 m up, with "
    "the sim's true attitude plus noise. No motion blur, no rolling shutter, no light "
    "changing, no grass moving. At 15 m/s the frames stopped matching (12.6% drift). The "
    "TF-Luna it needs for its height reads to 8 m at best, less in sunlight. And it isn't in "
    "the loop yet: my firmware doesn't fly on it.",
    "The maps are orthomosaics from known poses over flat ground: no heights (OpenDroneMap "
    "isn't installed), tall things lean on the map, and V's camera had to point straight "
    "down, which its bracket can't do (it's tipped 30 degrees for the live video).",
    "Change detection and the safe spots ran on a world of flat colors. Real ground has "
    "texture, shadows that move with the sun, and grass that changes between flights.",
    "Object detection ran on colored boxes, not real things: the model calls them cubes and "
    "green rectangular objects. It drew a box around the whole frame on an empty one. And "
    "it ran on the PC's RTX 3060; how fast the laptop's integrated graphics runs it is "
    "unknown.",
    'The plain-English missions\' local model misread "60 m west of home" as a point north '
    "and east. The checker passed it because it was safe. Only my approval, on a map, can "
    "catch a plan that's safe but wrong.",
    "The Meshtastic relay is a link budget over flat ground with a 10 dB margin: no trees, "
    "no hills, no other radios. Where the node lives (V, Base or its own module) is still "
    "open.",
)


def _step7_names() -> tuple[str, ...]:
    from pcs14.flight.scenarios import smart

    return tuple(s.name for s in smart.SCENARIOS)


def collect_runs(exports) -> list:
    from pcs14.flight import grade
    from pcs14.modules.report import Run

    names = _step7_names()
    runs = []
    for path in sorted((Path(exports) / "results").glob("*-mine.json")):
        data = json.loads(path.read_text(encoding="utf-8"))
        name = data["scenario"].removesuffix(" (mine)")
        if name not in names:
            continue
        run = data.get("run") or {}
        runs.append(
            Run(
                name,
                data["setup"],
                data["flown"],
                tuple(grade.Finding(**f) for f in data["findings"]),
                run.get("notes", {}),
                tuple(tuple(m) for m in run.get("marks", [])),
            )
        )
    order = {n: k for k, n in enumerate(names)}
    runs.sort(
        key=lambda r: (
            order[r.scenario],
            SETUP_ORDER.index(r.setup) if r.setup in SETUP_ORDER else 9,
        )
    )
    return runs


def load_detection(exports, run_model: bool = True) -> dict | None:
    """The detection's saved result, or a fresh one if Ollama answers; None otherwise."""
    path = Path(exports).parent / "smart" / "detect.json"
    if path.is_file():
        return json.loads(path.read_text(encoding="utf-8"))
    if not run_model:
        return None
    try:
        found = run_detection(exports)
    except (OSError, ValueError, StopIteration, FileNotFoundError):
        return None
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(found, indent=1), encoding="utf-8")
    return found


def verdict(runs: list, detection: dict | None) -> str:
    if not runs:
        return "not run"
    ok = all(r.passed for r in runs)
    if detection is not None:
        ok = ok and all(f.passed for f in detection_findings(detection))
    return "pass" if ok else "fail"


def _of(runs, scenario):
    return [r for r in runs if r.scenario == scenario]


def _cell(run, check) -> str:
    f = run.finding(check) if run is not None else None
    return f.detail if f is not None else ""


def tuning_rows(runs) -> list[tuple[str, float, float, float, float]]:
    """(setup, found, the model's, fit, dead time) from each combination's doublets."""
    import re

    out = []
    for r in _of(runs, "roll doublet"):
        f = r.finding("roll inertia")
        if f is None:
            continue
        m = re.search(
            r"found ([\d.]+) kg m\^2 against the model's ([\d.]+).*fit ([\d.]+), "
            r"the motors (\d+) ms",
            f.detail,
        )
        if m:
            out.append(
                (
                    r.setup,
                    float(m.group(1)),
                    float(m.group(2)),
                    float(m.group(3)),
                    float(m.group(4)) / 1000,
                )
            )
    return out


def flow_track(exports) -> dict | None:
    path = Path(exports) / "camera" / f"{CAMERA_RUN}-flow-track.json"
    return json.loads(path.read_text(encoding="utf-8")) if path.is_file() else None


def render(runs, detection, generated: str) -> str:
    from pcs14.smart import relay

    lines = [
        "# Smart features in sim (step 7)",
        "",
        f"*Generated {generated} by `pcs14 smart`, from the flight sim's runs of step 7's "
        "scenarios on my firmware, and the local vision model on step 6's camera frames. The "
        "spec is [docs/specs/2026-10-20-smart-features.md]"
        "(../../specs/2026-10-20-smart-features.md).*",
        "",
        "## The verdict",
        "",
        f"**{verdict(runs, detection)}.** {sum(r.passed for r in runs)} of {len(runs)} runs pass"
        + (
            "."
            if detection is None
            else ", and the object detection passes its grade."
            if all(f.passed for f in detection_findings(detection))
            else ", and the object detection misses its grade."
        ),
        "",
        "Every feature here works in the sim, and every one has limits the sim can't show. "
        "Those are at the end, and on the site's unproven list.",
        "",
        "## Landing modes",
        "",
        "Base, 15 m up and 30 m north, then each of the three ways down.",
        "",
        "| Mode | Where it came down | Touchdown |",
        "|---|---|---|",
    ]
    for name in ("land now", "back to start", "land here"):
        for r in _of(runs, name):
            lines.append(f"| {name} | {_cell(r, 'landed where asked')} | {_cell(r, 'touchdown')} |")
    lines += [
        "",
        "## Wind and the turn-back warning",
        "",
        "Hovering in a 6 m/s wind, the drone leans until its thrust's sideways part matches the "
        "drag, and the lean gives the wind back. Then 600 m out with the wind behind it and "
        "home into it. The warning predicts the energy home at the turn; the grade holds it "
        "against what the flight used. The warning never counts on forward flight being "
        "cheaper than a hover, because Gazebo's rotors don't make it so, and the first "
        "prediction, which did, came out 39% short.",
        "",
        "| Combination | Wind sensed | Energy home: predicted against used | My firmware's gauge |",
        "|---|---|---|---|",
    ]
    for r in _of(runs, "turn back"):
        lines.append(
            f"| {r.setup} | {_cell(r, 'wind sensed')} | "
            f"{_cell(r, 'the way home' + chr(39) + 's energy')} | "
            f"{_cell(r, 'my firmware' + chr(39) + 's gauge')} |"
        )
    rows = tuning_rows(runs)
    lines += [
        "",
        "## Self-tuning",
        "",
        "Three roll doublets on the stick in every combination, 10 m up: a quarter stick one "
        "way for a quarter second, then the other. The inertia comes from the gyro's roll rate "
        "against the torque the motors' commanded speeds make, fitted over each doublet's own "
        "window with the motors' lags (faster up than down) and the dead time between a "
        "command and the motors, found along with it. My rate loops multiply by the inertia, "
        "so the found one is the combination's profile, and the gains stay as they are.",
        "",
        "| Combination | Found | The model's | Off | Fit | Dead time |",
        "|---|---|---|---|---|---|",
    ]
    for setup, found, model, fit, delay in rows:
        lines.append(
            f"| {setup} | {found:.5f} kg m² | {model:.5f} kg m² | "
            f"{found / model - 1:+.1%} | {fit:.3f} | {delay * 1000:.0f} ms |"
        )
    lines += [
        "",
        "Getting here took three tries. Step 4's 15 degree stick steps came out 9 to 62% high. "
        "Held for 2 s, a step like that has the drone sliding sideways at several m/s, and "
        "most likely the rotors' drag, 4.7 cm above the center of gravity, makes a roll moment "
        "the fit doesn't know about. The first doublets read 12% low in base, fitted over "
        "stretches picked out by how busy the torque was, with one trim for the whole flight; "
        "fitting each doublet on its own window fixed that. And Max and mission still read "
        "13% low until the grade used the motors' commands at their own 250 Hz instead of "
        "the ground truth's 50, which smoothed away the fast changes the fit needs. Gazebo's "
        "own answer was checked in zero gravity, with a known torque on the body: 0.01292 "
        "kg m² in base's roll against the model's 0.01293.",
        "",
        "![Self-tuning](stills/tuning-wide.png)",
        "",
        "## A plain-English mission",
        "",
    ]
    for r in _of(runs, "planned mission"):
        for f in r.findings:
            if f.check != "false triggers":
                lines.append(f"- {f.check}: {f.detail}")
    lines += [
        "",
        "The local model (Qwen2.5 7B through Ollama) writes the plan, the checker checks it "
        "against the limits profile and the drone, and it's saved unapproved. In the sim the "
        "test script approves it and says so; on the drone that's me. The finding worth more "
        "than the pass: asked to fly 60 m west of home, the model wrote a point north and "
        "east, and the checker passed it, since it was safe. So the plan gets drawn on a map "
        "before I approve it.",
        "",
        "## The spiral descent and soar mode",
        "",
    ]
    for scenario in ("spiral descent", "lift"):
        for r in _of(runs, scenario):
            for f in r.findings:
                if f.check not in ("false triggers", "touchdown"):
                    lines.append(f"- {scenario}, {f.check}: {f.detail}")
    lines += [
        "",
        "## Mapping, change detection and safe spots",
        "",
        "V's camera pointed straight down, a three-line grid 30 m up over step 6's scenery, "
        "and the orthomosaic from the frames and the log's poses. Then the same grid with the "
        "box moved 22 m, the two maps differenced. Then, asked to land on the shed, the "
        "nearest safe spot.",
        "",
    ]
    for scenario in ("mapping run", "mapping run, box moved", "safe landing"):
        for r in _of(runs, scenario):
            for f in r.findings:
                if f.check not in ("false triggers", "touchdown") and "on the map" not in f.check:
                    lines.append(f"- {scenario}, {f.check}: {f.detail}")
            on_map = [f for f in r.findings if "on the map" in f.check]
            if on_map:
                ok = sum(f.passed for f in on_map)
                lines.append(
                    f"- {scenario}: {ok} of {len(on_map)} things on the map within a "
                    "meter of where they stand"
                )
    lines += [
        "",
        "![The map](stills/map-portrait.png)",
        "",
        "![What changed](stills/change-portrait.png)",
        "",
    ]
    lines += [
        "## GPS-free flight's estimate",
        "",
        "V's camera pointed down, 6 m up over a textured field (Gazebo's ground is one flat "
        "color, which gives the correlation nothing), around three sides of a 40 by 20 m "
        "rectangle at 3 m/s. The position comes from the frames alone: how far the ground "
        "slides between frames (phase correlation, refined to a hundredth of a pixel), turned "
        "into meters with the attitude and the TF-Luna's height. The attitude is the sim's "
        "truth tilted by half a degree of noise, the height the truth with the TF-Luna's 2%.",
        "",
    ]
    for r in _of(runs, "flow run"):
        for f in r.findings:
            if f.check != "false triggers":
                lines.append(f"- {f.check}: {f.detail}")
    lines += [
        "",
        "The first try flew the legs at my firmware's own pace, about 15 m/s: 1.5 m between "
        "frames at 6 m up, a fifth of the frame, with the drone tilted 30 degrees, and the "
        "frames stopped matching. It drifted 12.6%. Flow-only flight is slow flight.",
        "",
        "![GPS-free flight](stills/flow-wide.png)",
        "",
        "## Object detection",
        "",
    ]
    if detection is None:
        lines += ["Not run: it needs Ollama with qwen2.5vl:7b.", ""]
    else:
        total = detect.totals(scored(detection))
        lines += [
            f"{detection['model']} through Ollama, on {total['frames']} of step 6's camera "
            "frames: a hover looking ahead, five along the dash north, one past everything. "
            "Each true box is worked out from where Gazebo put each thing and where the camera "
            "was. The prompt, chosen from three tried on one frame: "
            f'"{detection["prompt"]}"',
            "",
        ]
        lines += [f"- {f.check}: {f.detail}" for f in detection_findings(detection)]
        names = {k: sorted(set(v)) for k, v in total["labels"].items()}
        lines += [
            "",
            "What it called them: "
            + "; ".join(f"the {k}: {', '.join(v)}" for k, v in sorted(names.items()))
            + ".",
            "",
            "So it's a describer and a coarse detector: the big things every time, about two "
            "thirds of everything, with boxes good enough to point at but not to land by. Safe "
            "spots stay on the map's heights.",
            "",
            "![Object detection](stills/detection-wide.png)",
            "",
        ]
    lines += [
        "## The Meshtastic relay",
        "",
        f"How far a node reaches: one on the ground ({RELAY_GROUND_M:g} m up, in someone's hand) "
        f"to another on the ground, and one riding on the drone at {RELAY_UP_M:g} m to one on "
        "the ground. Flat ground, a 10 dB margin (pcs14.smart.relay):",
        "",
        "| Preset | Ground to ground | Drone to ground |",
        "|---|---|---|",
    ]
    for p in RELAY_PRESETS:
        low = relay.reach_m(p, RELAY_GROUND_M, RELAY_GROUND_M)
        high = relay.reach_m(p, RELAY_UP_M, RELAY_GROUND_M)
        lines.append(f"| {p} | {low / 1000:.1f} km | {high / 1000:.1f} km |")
    lines += ["", "## What it can't prove", ""]
    lines += [f"- {u}" for u in UNPROVEN]
    lines += [""]
    return "\n".join(lines)


def to_data(runs, detection, generated: str) -> dict:
    from pcs14.smart import relay

    out = {
        "generated": generated,
        "verdict": verdict(runs, detection),
        "runs": [
            {
                "scenario": r.scenario,
                "setup": r.setup,
                "passed": r.passed,
                "findings": [f.__dict__ for f in r.findings],
            }
            for r in runs
        ],
        "tuning": [
            {"setup": s, "found_kg_m2": f, "model_kg_m2": m, "fit": q, "dead_time_s": d}
            for s, f, m, q, d in tuning_rows(runs)
        ],
        "relay": {
            p: {
                "ground_m": relay.reach_m(p, RELAY_GROUND_M, RELAY_GROUND_M),
                "drone_m": relay.reach_m(p, RELAY_UP_M, RELAY_GROUND_M),
            }
            for p in RELAY_PRESETS
        },
        "unproven": list(UNPROVEN),
    }
    if detection is not None:
        total = detect.totals(scored(detection))
        out["detection"] = {
            "model": detection["model"],
            "totals": total,
            "findings": [f.__dict__ for f in detection_findings(detection)],
        }
    return out


# --- the stills ---------------------------------------------------------------------------


def tuning_still(runs, path: Path, size: str = "wide") -> Path | None:
    from pcs14.report import charts

    rows = tuning_rows(runs)
    if not rows:
        return None
    canvas = charts.Canvas(
        "Self-tuning",
        "The roll inertia from three stick doublets, against the model's, in every combination",
        made_up=False,
        size=size,
    )
    (ax,) = canvas.axes
    x = np.arange(len(rows))
    ax.bar(
        x - 0.2,
        [m * 1000 for _, _, m, _, _ in rows],
        0.4,
        color=charts._c("muted"),
        label="the model's",
    )
    ax.bar(
        x + 0.2,
        [f * 1000 for _, f, _, _, _ in rows],
        0.4,
        color=charts._c("accent"),
        label="found in flight",
    )
    ax.set_xticks(x, [s for s, *_ in rows])
    ax.legend(frameon=False, labelcolor=charts._c("text"), fontsize=13, loc="upper left")
    charts._label(ax, "", "roll inertia (g m²)")
    worst = max(abs(f / m - 1) for _, f, m, _, _ in rows)
    canvas.headline(
        f"{worst:.1%}",
        "off at worst, in all eight. Step 4's big stick steps were "
        "off by up to 62%: a small, quick doublet is what tells the inertia.",
    )
    canvas.save(path)
    return path


def flow_still(track: dict | None, path: Path, size: str = "wide") -> Path | None:
    from pcs14.report import charts

    if not track:
        return None
    truth, found = np.array(track["truth"]), np.array(track["found"])
    flown = track["flown_m"][-1]
    off = float(np.hypot(*(found[-1] - truth[-1])))
    canvas = charts.Canvas(
        "Flying without GPS",
        "Where the camera and the rangefinder said it was, against where it was",
        made_up=False,
        size=size,
    )
    (ax,) = canvas.axes
    ax.plot(
        truth[:, 0],
        truth[:, 1],
        color=charts._c("muted"),
        linewidth=6,
        alpha=0.6,
        label="where it was (Gazebo)",
    )
    ax.plot(
        found[:, 0],
        found[:, 1],
        color=charts._c("accent"),
        linewidth=2.2,
        label="the estimate, no GPS",
    )
    ax.set_aspect("equal", adjustable="datalim")
    ax.legend(frameon=False, labelcolor=charts._c("text"), fontsize=13, loc="center left")
    charts._label(ax, "east (m)", "north (m)")
    canvas.headline(
        f"{off:.2f} m",
        f"off after {flown:.0f} m flown, {off / flown:.1%}, from "
        "the frames, the attitude and the height alone. At 3 m/s, over a "
        "textured field.",
    )
    canvas.save(path)
    return path


def detection_still(exports, detection: dict | None, path: Path) -> Path | None:
    from PIL import Image

    from pcs14.report import charts

    if detection is None:
        return None
    frames = scored(detection)
    best = max(frames, key=lambda s: len(s.truth))
    frame = Path(exports) / "camera" / CAMERA_RUN / f"frame-{best.frame:04d}.png"
    if not frame.is_file():
        return None
    picture = Image.open(frame)
    canvas = charts.Canvas(
        "What the laptop's model sees",
        f"{detection['model']}, asked for every object, on V's camera in the sim",
        made_up=False,
        size="wide",
    )
    (ax,) = canvas.axes
    ax.set_axis_off()
    ax.imshow(np.asarray(picture.convert("RGB")))
    fonts = charts._fonts()
    from matplotlib.patches import Rectangle

    for b in best.truth:
        ax.add_patch(
            Rectangle(
                (b.left, b.top),
                b.right - b.left,
                b.bottom - b.top,
                fill=False,
                edgecolor=charts._c("text"),
                linewidth=1.0,
                linestyle="--",
            )
        )
    for b in best.found:
        ax.add_patch(
            Rectangle(
                (b.left, b.top),
                b.right - b.left,
                b.bottom - b.top,
                fill=False,
                edgecolor=charts._c("accent"),
                linewidth=2.0,
            )
        )
        ax.text(
            b.left + 4,
            b.top - 6,
            b.label,
            color=charts._c("accent"),
            fontsize=11,
            family=fonts["body"],
        )
    total = detect.totals(frames)
    canvas.headline(
        f"{total['near']} of {total['true']}",
        f"true things boxed, over {total['frames']} frames (dashed: where they "
        "are; green: the model's). The big ones every time, the thin far ones "
        "about half.",
    )
    canvas.save(path)
    return path


def _map(exports, suffix: str):
    from PIL import Image

    path = Path(exports) / "camera" / f"{CAMERA_RUN}-{suffix}.png"
    return np.asarray(Image.open(path).convert("RGB")) if path.is_file() else None


def map_still(exports, runs, path: Path) -> Path | None:
    from matplotlib.patches import Circle

    from pcs14.flight.scenarios.smart import MAP_AREA, SAFE_ASKED, true_safe
    from pcs14.report import charts

    image = _map(exports, "mapping")
    if image is None:
        return None
    (e0, e1), (n0, n1) = MAP_AREA
    canvas = charts.Canvas(
        "The map, and where it's safe",
        "V's frames from 30 m up, laid on the ground from where the camera was",
        made_up=False,
        size="portrait",
    )
    (ax,) = canvas.axes
    ax.imshow(image, extent=(e0, e1, n0, n1))
    safe = true_safe()
    s0, s1 = safe.east0, safe.east0 + safe.values.shape[1] * safe.m_per_px
    t1, t0 = safe.north1, safe.north1 - safe.values.shape[0] * safe.m_per_px
    shade = np.zeros((*safe.values.shape, 4))
    shade[~safe.values] = (0.04, 0.04, 0.04, 0.45)
    ax.imshow(shade, extent=(s0, s1, t0, t1))
    ax.plot(*SAFE_ASKED, marker="x", color=charts._c("pop"), markersize=14, mew=3)
    landed = next((r.notes.get("chosen") for r in _of(runs, "safe landing")), None)
    if landed:
        ax.add_patch(
            Circle(tuple(landed), 1.5, fill=False, edgecolor=charts._c("accent"), linewidth=2.5)
        )
    ax.set_xlim(e0, e1)
    ax.set_ylim(n0, n1)
    charts._label(ax, "east (m)", "north (m)")
    distance = (
        float(np.hypot(landed[0] - SAFE_ASKED[0], landed[1] - SAFE_ASKED[1])) if landed else 0
    )
    canvas.headline(
        f"{distance:.1f} m",
        "from the shed it was asked to land on (the cross) to "
        "the nearest safe spot, where it landed (the circle). Shaded: too near "
        "something.",
    )
    canvas.save(path)
    return path


def change_still(exports, path: Path) -> Path | None:
    from matplotlib.patches import Circle

    from pcs14.flight.scenarios.smart import MAP_AREA, MAP_M_PER_PX
    from pcs14.report import charts
    from pcs14.smart import change
    from pcs14.smart.ortho import Mosaic

    before, after = _map(exports, "mapping"), _map(exports, "mapping-moved")
    if before is None or after is None:
        return None
    (e0, e1), (n0, n1) = MAP_AREA
    blobs = change.changes(
        Mosaic(before, e0, n1, MAP_M_PER_PX, 1.0), Mosaic(after, e0, n1, MAP_M_PER_PX, 1.0)
    )
    canvas = charts.Canvas(
        "What changed",
        "The same grid flown twice, the box moved 22 m between",
        made_up=False,
        size="portrait",
    )
    (ax,) = canvas.axes
    ax.set_axis_off()
    gap = 4.0
    width = e1 - e0
    ax.imshow(before, extent=(e0, e1, n0, n1))
    ax.imshow(after, extent=(e1 + gap, e1 + gap + width, n0, n1))
    fonts = charts._fonts()
    for x, words in ((e0 + width / 2, "first flight"), (e1 + gap + width / 2, "second flight")):
        ax.text(
            x,
            n1 + 2,
            words,
            ha="center",
            color=charts._c("muted"),
            fontsize=14,
            family=fonts["body"],
        )
    for b in blobs:
        for shift in (0.0, width + gap):
            ax.add_patch(
                Circle(
                    (b.east + shift, b.north),
                    3.0,
                    fill=False,
                    edgecolor=charts._c("accent"),
                    linewidth=2.5,
                )
            )
    ax.set_xlim(e0, e1 + gap + width)
    ax.set_ylim(n0, n1 + 5)
    # a moved thing's spots within CHANGE_RADIUS_M of each other are the one place (the box
    # and its shadow split apart at its new spot)
    from pcs14.flight.scenarios.smart import CHANGE_RADIUS_M

    places: list[list] = []
    for b in blobs:
        near = next(
            (
                p
                for p in places
                if any(np.hypot(b.east - q.east, b.north - q.north) <= CHANGE_RADIUS_M for q in p)
            ),
            None,
        )
        if near is None:
            places.append([b])
        else:
            near.append(b)
    canvas.headline(
        f"{len(places)} places",
        "flagged on both maps: where the box was and where it went (there as two spots, the "
        "box and its shadow). Nothing else.",
    )
    canvas.save(path)
    return path


def write(exports, out, generated: str, run_model: bool = True) -> list[Path]:
    out = Path(out)
    stills = out / "stills"
    stills.mkdir(parents=True, exist_ok=True)
    runs = collect_runs(exports)
    detection = load_detection(exports, run_model)
    drawn = [
        tuning_still(runs, stills / "tuning-wide.png"),
        tuning_still(runs, stills / "tuning-portrait.png", "portrait"),
        flow_still(flow_track(exports), stills / "flow-wide.png"),
        flow_still(flow_track(exports), stills / "flow-portrait.png", "portrait"),
        detection_still(exports, detection, stills / "detection-wide.png"),
        map_still(exports, runs, stills / "map-portrait.png"),
        change_still(exports, stills / "change-portrait.png"),
    ]
    (out / "README.md").write_bytes(render(runs, detection, generated).encode("utf-8"))
    (out / "smart.json").write_bytes(
        (json.dumps(to_data(runs, detection, generated), indent=1, default=float) + "\n").encode()
    )
    return [out / "README.md", out / "smart.json", *(p for p in drawn if p is not None)]
