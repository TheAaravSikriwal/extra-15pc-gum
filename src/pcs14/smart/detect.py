"""Object detection (#22): a local vision model (qwen2.5vl:7b through Ollama, on the laptop or
the PC, nothing in the cloud) asked what's in V's frames and where, and its boxes checked
against where Gazebo put each thing.

The truth is worked out, not drawn by hand: each scenery box's eight corners projected into the
frame from the camera's pose at that moment (pcs14.smart.ortho), and the rectangle around
them. That rectangle is a little bigger than the box looks, which a model's tight box loses a
bit of overlap to. Nothing is checked for being hidden behind something else; in the camera
run's view nothing is.

Qwen2.5-VL answers in pixels of the picture it was given, after its own resizing to multiples
of 28. The picture goes in already that size, so its pixels map straight back.
"""

import base64
import io
import json
import re
from dataclasses import dataclass

import numpy as np

MODEL = "qwen2.5vl:7b"
HOST = "http://127.0.0.1:11434"
GRID = 28  # Qwen2.5-VL's patch size: pictures go in as multiples of it
MIN_SIDE_PX = 12  # true boxes narrower than this in the frame are too far to grade
# of three tried on the same frame (2026-10-21): asking for "every object standing on the
# ground" found only the shed; Qwen's own grounding prompt boxed 5 of 7 but called all of them
# "object"; this one boxed 4 of 7 and named them (brown cube, pink cube, green rectangular
# object)
PROMPT = (
    "Locate every object in this image, however small, and output their bbox coordinates in "
    "JSON format with a label for each."
)


@dataclass(frozen=True)
class Box:
    label: str
    left: float
    top: float
    right: float
    bottom: float

    @property
    def area(self) -> float:
        return max(0.0, self.right - self.left) * max(0.0, self.bottom - self.top)


def parse(reply: str, scale: tuple[float, float]) -> list[Box]:
    """The boxes in a model's reply, scaled by (x, y) back to the frame's pixels. Anything
    that isn't a label with four numbers is left out."""
    start, end = reply.find("["), reply.rfind("]")
    if start < 0 or end <= start:
        return []
    try:
        items = json.loads(reply[start : end + 1])
    except json.JSONDecodeError:
        # a list of lists can confuse the slice: take the objects one by one
        items = [json.loads(m) for m in re.findall(r"\{[^{}]*\}", reply)]
    sx, sy = scale
    out = []
    for item in items if isinstance(items, list) else []:
        box = item.get("bbox_2d") if isinstance(item, dict) else None
        if not (isinstance(box, list) and len(box) == 4):
            continue
        x1, y1, x2, y2 = (float(v) for v in box)
        out.append(Box(str(item.get("label", "")), x1 * sx, y1 * sy, x2 * sx, y2 * sy))
    return out


def iou(a: Box, b: Box) -> float:
    """Intersection over union: the area two boxes share over the area they cover."""
    shared = Box("", max(a.left, b.left), max(a.top, b.top), min(a.right, b.right),
                 min(a.bottom, b.bottom)).area  # fmt: skip
    covered = a.area + b.area - shared
    return shared / covered if covered > 0 else 0.0


def truth_boxes(camera, pose, scenery) -> list[Box]:
    """Where each scenery box (name, middle, size, color: Gazebo's frame) shows in the frame,
    clipped to it; boxes behind the camera, off the frame or too small to grade are left out."""
    out = []
    for name, middle, size, _color in scenery:
        half = np.asarray(size, dtype=float) / 2
        signs = np.array([[x, y, z] for x in (-1, 1) for y in (-1, 1) for z in (-1, 1)])
        rows, cols = camera.project(pose, np.asarray(middle, dtype=float) + signs * half)
        if np.isnan(rows).any():
            continue
        right, bottom = min(camera.width - 1.0, cols.max()), min(camera.height - 1.0, rows.max())
        box = Box(name, max(0.0, cols.min()), max(0.0, rows.min()), right, bottom)
        if min(box.right - box.left, box.bottom - box.top) >= MIN_SIDE_PX:
            out.append(box)
    return out


def match(truth: list[Box], found: list[Box]) -> list[tuple[Box, Box | None, float]]:
    """Each true box with the found box it overlaps most (each found box used once, the best
    overlaps first), or None where nothing found overlaps it."""
    pairs = sorted(((iou(t, f), i, j) for i, t in enumerate(truth) for j, f in enumerate(found)),
                   reverse=True)  # fmt: skip
    best: dict[int, tuple[int, float]] = {}
    used = set()
    for overlap, i, j in pairs:
        if overlap <= 0 or i in best or j in used:
            continue
        best[i] = (j, overlap)
        used.add(j)
    return [(t, found[best[i][0]], best[i][1]) if i in best else (t, None, 0.0)
            for i, t in enumerate(truth)]  # fmt: skip


def _post(body: dict, host: str = HOST) -> str:
    import urllib.request

    request = urllib.request.Request(f"{host}/api/chat", data=json.dumps(body).encode(),
                                     headers={"Content-Type": "application/json"})  # fmt: skip
    with urllib.request.urlopen(request, timeout=300) as reply:
        return json.loads(reply.read())["message"]["content"]


def ask(picture, model: str = MODEL, post=_post) -> list[Box]:
    """What the model finds in a frame, in the frame's own pixels."""
    from PIL import Image

    image = Image.fromarray(np.asarray(picture, dtype=np.uint8)[:, :, :3])
    w, h = image.size
    w2, h2 = (max(GRID, round(v / GRID) * GRID) for v in (w, h))
    buffer = io.BytesIO()
    image.resize((w2, h2), Image.BICUBIC).save(buffer, format="PNG")
    body = {
        "model": model,
        "messages": [{"role": "user", "content": PROMPT,
                      "images": [base64.b64encode(buffer.getvalue()).decode()]}],
        "stream": False,
        "options": {"temperature": 0},
    }  # fmt: skip
    return parse(post(body), scale=(w / w2, h / h2))


NEAR_IOU = 0.3  # looser than COCO's 0.5: the true box is the corners' rectangle, a bit big


@dataclass
class Scored:
    """One frame: the true boxes, the model's, and how they pair up."""

    frame: int
    truth: list
    found: list

    @property
    def pairs(self) -> list:
        return match(self.truth, self.found)

    @property
    def near(self) -> list:
        """The true things the model put a box near (overlap at least NEAR_IOU)."""
        return [p for p in self.pairs if p[2] >= NEAR_IOU]

    @property
    def false_alarms(self) -> list:
        """The model's boxes that overlap nothing true at all."""
        return [f for f in self.found if all(iou(t, f) == 0 for t in self.truth)]


def totals(scored: list) -> dict:
    """The run's numbers: true things, how many got a near box, the overlaps, false alarms, and
    what the model called each kind of thing (tree_0 and tree_1 are both trees)."""
    labels: dict = {}
    overlaps = []
    for s in scored:
        for t, f, overlap in s.pairs:
            if f is not None:
                labels.setdefault(t.label.split("_")[0], []).append(f.label)
            if overlap >= NEAR_IOU:
                overlaps.append(overlap)
    return {
        "frames": len(scored),
        "true": sum(len(s.truth) for s in scored),
        "near": sum(len(s.near) for s in scored),
        "median overlap": float(np.median(overlaps)) if overlaps else None,
        "false alarms": sum(len(s.false_alarms) for s in scored),
        "labels": labels,
    }
