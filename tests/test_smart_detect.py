"""Object detection (#22): a local vision model's boxes on V's frames, against boxes worked out
from where Gazebo put each thing and where the camera was."""

import numpy as np
import pytest

from pcs14.smart import detect, ortho


def test_the_models_reply_is_read_with_or_without_a_code_fence():
    reply = """Here you go:
```json
[{"bbox_2d": [10, 20, 110, 220], "label": "shed"}, {"bbox_2d": [5, 5, 9, 9], "label": "box"}]
```"""
    found = detect.parse(reply, scale=(2.0, 0.5))
    assert found[0] == detect.Box("shed", 20.0, 10.0, 220.0, 110.0)
    assert [b.label for b in found] == ["shed", "box"]
    assert detect.parse("no objects, sorry", scale=(1.0, 1.0)) == []
    assert detect.parse('[{"label": "tree"}]', scale=(1.0, 1.0)) == []  # no box, no detection


def test_overlap_is_area_shared_over_area_covered():
    a = detect.Box("a", 0, 0, 10, 10)
    assert detect.iou(a, detect.Box("b", 0, 0, 10, 10)) == pytest.approx(1.0)
    assert detect.iou(a, detect.Box("b", 5, 0, 15, 10)) == pytest.approx(50 / 150)
    assert detect.iou(a, detect.Box("b", 20, 20, 30, 30)) == 0.0


def test_a_box_in_front_of_the_camera_lands_where_it_stands():
    camera = ortho.Camera(width=640, height=360, hfov_rad=1.15192)
    level = np.array([0.0, 0.0, np.sqrt(0.5), np.sqrt(0.5)])  # facing north
    pose = ortho.Pose.on_drone((0.0, 0.0, 2.0), level)
    scenery = [("cube", (0.0, 20.0, 2.0), (2.0, 2.0, 2.0), (1, 0, 0)),
               ("behind", (0.0, -20.0, 2.0), (2.0, 2.0, 2.0), (1, 0, 0))]  # fmt: skip
    boxes = detect.truth_boxes(camera, pose, scenery)
    assert [b.label for b in boxes] == ["cube"]
    cube = boxes[0]
    cy, cx = camera.center
    middle_col, middle_row = (cube.left + cube.right) / 2, (cube.top + cube.bottom) / 2
    assert middle_col == pytest.approx(cx, abs=1.0) and middle_row == pytest.approx(cy, abs=1.0)
    # 2 m wide at 19 to 21 m away: the near face's width, about 2 / 19 of the focal length
    assert cube.right - cube.left == pytest.approx(2 / 19 * camera.focal_px, rel=0.05)


def test_each_true_thing_is_matched_to_the_found_box_it_overlaps_most():
    truth = [detect.Box("shed", 0, 0, 100, 100), detect.Box("box", 200, 200, 220, 220)]
    found = [detect.Box("house", 10, 10, 100, 110), detect.Box("crate", 400, 400, 420, 420)]
    pairs = detect.match(truth, found)
    assert pairs[0][1].label == "house" and pairs[0][2] > 0.7
    assert pairs[1][1] is None  # the crate overlaps nothing true


def test_asking_sends_the_picture_sized_to_the_models_grid(monkeypatch):
    sent = {}

    def fake(body: dict) -> str:
        sent.update(body)
        return '[{"bbox_2d": [0, 0, 644, 364], "label": "everything"}]'

    picture = np.zeros((360, 640, 3), dtype=np.uint8)
    found = detect.ask(picture, post=fake)
    message = sent["messages"][0]
    assert message["images"] and "JSON" in message["content"]
    # 640 x 360 goes to the model as 644 x 364 (multiples of 28), and its pixels come back
    assert found[0].right == pytest.approx(640.0) and found[0].bottom == pytest.approx(360.0)


def test_a_frames_score_counts_near_boxes_and_false_alarms():
    truth = [detect.Box("shed", 0, 0, 100, 100), detect.Box("box", 200, 200, 230, 230)]
    found = [detect.Box("brown cube", 5, 5, 100, 100), detect.Box("pink cube", 180, 200, 210, 230),
             detect.Box("person", 600, 600, 620, 620)]  # fmt: skip
    scored = detect.Scored(frame=7, truth=truth, found=found)
    assert [t.label for t, _, _ in scored.near] == ["shed"]  # the pink cube is off by 20 px
    assert [b.label for b in scored.false_alarms] == ["person"]  # overlaps nothing true
    total = detect.totals([scored, detect.Scored(frame=8, truth=[], found=[])])
    assert total["true"] == 2 and total["near"] == 1 and total["false alarms"] == 1
    assert total["frames"] == 2 and total["labels"]["shed"] == ["brown cube"]
