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
