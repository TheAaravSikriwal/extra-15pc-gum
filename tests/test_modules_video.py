"""The live video at the rate HaLow holds: the bitrate budget, and frames encoded to it with
ffmpeg (skipped where there's no ffmpeg)."""

import pytest

from pcs14.modules import video


def test_the_video_gets_what_the_link_holds_less_the_overhead_and_the_telemetry():
    # 2.9 Mbps on the air, about 60% of it carries data, less the telemetry's 0.1 Mbps
    assert video.budget_kbps(2.9) == pytest.approx(2.9e3 * 0.6 - 100, abs=1)
    assert video.budget_kbps(0.0) == 0
    assert video.budget_kbps(0.1) == 0  # nothing left for video at the very edge


def test_each_distance_gets_its_bitrate_and_what_that_carries():
    rows = video.at_distances((100, 3000, 9000), height_m=30.0)
    assert [r.distance_m for r in rows] == [100, 3000, 9000]
    assert rows[0].kbps > rows[1].kbps > rows[2].kbps == 0
    assert rows[0].carries.startswith("720p")
    assert rows[2].carries == "no video"


def test_the_comparison_gives_each_distance_its_resolution_and_bits():
    found = video.comparison(height_m=30.0)
    assert [c.distance_m for c in found] == list(video.COMPARE_M)
    assert found[0].lines == 720 and found[-1].lines < found[0].lines
    # frames saved at 10 a second each get the bits they'd get at 30
    assert found[0].kbps_at_10 == pytest.approx(found[0].row.kbps / 3)


@pytest.mark.skipif(video.ffmpeg() is None, reason="no ffmpeg here")
def test_frames_encode_at_the_budget(tmp_path):
    import numpy as np
    from PIL import Image

    rng = np.random.default_rng(4)
    base = (rng.random((360, 640, 3)) * 255).astype("uint8")
    for k in range(60):  # 2 s at 30 frames a second, a scene panning sideways
        Image.fromarray(np.roll(base, 4 * k, axis=1)).save(tmp_path / f"frame-{k:04d}.png")
    out = video.encode(tmp_path, tmp_path / "clip.mp4", kbps=800, fps=30)
    assert out.is_file()
    measured = out.stat().st_size * 8 / 1000 / 2.0  # kbit/s over the 2 s
    assert measured < 800 * 1.3
