"""The camera recorder: every frame it took gets written, however slow the writing is, and a
folder left over from an earlier run doesn't leak old frames into this one."""

import time
from types import SimpleNamespace

import numpy as np

from pcs14.flight.run import CameraRecorder


class FakeTopics:
    def __init__(self):
        self.callback = None
        self.node = SimpleNamespace(subscribe=self._subscribe)

    def _kind(self, name):
        return name

    def _subscribe(self, kind, topic, callback):
        self.callback = callback


def image(t: float, value: int):
    data = np.full((4, 6, 3), value, dtype=np.uint8).tobytes()
    stamp = SimpleNamespace(sec=int(t), nsec=int(round((t - int(t)) * 1e9)))
    return SimpleNamespace(header=SimpleNamespace(stamp=stamp), height=4, width=6, data=data)


class SlowRecorder(CameraRecorder):
    def _write(self, path, frame):
        time.sleep(0.03)  # a textured 1280 by 720 PNG takes about 0.2 s
        super()._write(path, frame)


def test_every_frame_taken_is_written_before_close_returns(tmp_path):
    topics = FakeTopics()
    recorder = SlowRecorder(topics, "/camera", tmp_path, every=2)
    start = time.monotonic()
    for k in range(40):
        topics.callback(image(k * 0.1, k))
    # Gazebo's transport calls back on its own thread, one message at a time: the callback
    # has to hand the writing off, or the frames pile up where close can't reach them
    assert time.monotonic() - start < 0.2
    recorder.close()
    times = (tmp_path / "frames.txt").read_text().split()
    assert len(times) == 20 == len(recorder.saved)
    assert sorted(p.name for p in tmp_path.glob("frame-*.png"))[-1] == "frame-0019.png"
    from PIL import Image

    assert np.asarray(Image.open(tmp_path / "frame-0003.png"))[0, 0, 0] == 6


def test_an_earlier_runs_frames_are_cleared(tmp_path):
    (tmp_path / "frame-0500.png").write_bytes(b"old")
    topics = FakeTopics()
    recorder = CameraRecorder(topics, "/camera", tmp_path)
    recorder.close()
    assert not (tmp_path / "frame-0500.png").exists()
