"""Module V's live video at the rate HaLow holds: what's left of the link for video at each
distance, what that carries, and frames encoded to it with ffmpeg (H.264, the way the Pi 5 would
in software), so the picture against range is something to look at.

The link carries about 60% of its PHY rate as data once the MAC's framing, acknowledgements and
gaps are paid for (a rough figure for 802.11 at these rates, not a measurement), and the
telemetry takes 0.1 Mbps of that.
"""

import shutil
import subprocess
from dataclasses import dataclass
from pathlib import Path

from pcs14.modules import halow

DATA_SHARE = 0.6  # of the PHY rate, after the MAC's overhead
TELEMETRY_KBPS = 100.0
# what a bitrate carries, the least first that's watchable (H.264 at 30 frames a second)
CARRIES = ((2000, "720p at 30 frames a second"), (900, "480p at 30 frames a second"),
           (400, "360p at 15 frames a second"), (150, "240p at 10 frames a second"))  # fmt: skip


def budget_kbps(phy_mbps: float) -> float:
    return max(0.0, phy_mbps * 1000 * DATA_SHARE - TELEMETRY_KBPS)


def carries(kbps: float) -> str:
    return next((words for floor, words in CARRIES if kbps >= floor), "no video")


@dataclass(frozen=True)
class Row:
    distance_m: float
    phy_mbps: float
    kbps: float
    carries: str


def at_distances(distances, height_m: float, link: halow.Link | None = None) -> list[Row]:
    link = link or halow.Link()
    rows = []
    for d in distances:
        phy = link.rate_mbps(d, height_m)
        kbps = budget_kbps(phy)
        rows.append(Row(d, phy, kbps, carries(kbps)))
    return rows


COMPARE_M = (1000, 3000, 5000)  # the distances the report's still puts side by side
SAVED_FPS = 10  # the camera scenario saves every third of its 30 frames a second
LINES = {"720p": 720, "480p": 480, "360p": 360, "240p": 240}


@dataclass(frozen=True)
class Compared:
    row: Row
    lines: int  # the resolution it carries

    @property
    def distance_m(self) -> float:
        return self.row.distance_m

    @property
    def kbps_at_10(self) -> float:
        """The bitrate for frames saved at 10 a second, each with its share at 30 (240p's
        budget is already at 10 frames a second)."""
        return self.row.kbps if self.lines <= 240 else self.row.kbps * SAVED_FPS / 30


def comparison(height_m: float = 30.0) -> list[Compared]:
    out = []
    for row in at_distances(COMPARE_M, height_m):
        lines = next((v for k, v in LINES.items() if row.carries.startswith(k)), 0)
        out.append(Compared(row, lines))
    return out


def ffmpeg() -> str | None:
    return shutil.which("ffmpeg")


def encode(frames: Path, out: Path, kbps: float, fps: int = 30, pattern: str = "frame-%04d.png",
           height: int | None = None) -> Path:  # fmt: skip
    """The frames in `frames` (named by `pattern`) as H.264 held to `kbps`, scaled to `height`
    lines if given."""
    tool = ffmpeg()
    if tool is None:
        raise RuntimeError("no ffmpeg on this machine")
    scale = ["-vf", f"scale=-2:{height}"] if height else []
    rate = f"{int(kbps)}k"
    source = str(Path(frames) / pattern)
    subprocess.run(
        [tool, "-y", "-loglevel", "error", "-framerate", str(fps), "-i", source, *scale,
         "-c:v", "libx264", "-preset", "veryfast", "-tune", "zerolatency",
         "-b:v", rate, "-maxrate", rate, "-bufsize", f"{int(kbps // 2)}k",
         "-pix_fmt", "yuv420p", str(out)],
        check=True,
    )  # fmt: skip
    return Path(out)
