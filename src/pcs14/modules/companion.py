"""Module V's companion computer: the jobs that have to stay on the drone, against what a
Raspberry Pi 5 and a Jetson Orin Nano can do, from what their makers and published benchmarks
say. Nothing here is measured on a board: there's no board to measure. Every number has its
source next to it.

The jobs that left the drone are why this is close: the LLM and the object detector run on the
laptop (decisions.md), so a GPU on board would mostly sit idle.
"""

from dataclasses import dataclass


@dataclass(frozen=True)
class Fact:
    what: str
    value: str
    source: str


@dataclass(frozen=True)
class Board:
    name: str
    hardware_encoder: bool
    facts: tuple[Fact, ...]


@dataclass(frozen=True)
class Job:
    name: str
    why_on_board: str
    need: str
    source: str


PI_WHITE_PAPER = (
    "https://pip-assets.raspberrypi.com/categories/685-app-notes-guides-whitepapers/documents/"
    "RP-010033-WP-1-H.264%20encoding%20performance%20on%20Raspberry%20Pi%205_series%20computers.pdf"
)
NVIDIA_SW_ENCODE = (
    "https://docs.nvidia.com/jetson/archives/r36.3/DeveloperGuide/SD/Multimedia/"
    "SoftwareEncodeInOrinNano.html"
)
NVIDIA_SUPER = (
    "https://developer.nvidia.com/blog/"
    "nvidia-jetpack-6-2-brings-super-mode-to-nvidia-jetson-orin-nano-and-jetson-orin-nx-modules"
)
VIO_BENCHMARK = "https://rpg.ifi.uzh.ch/docs/ICRA18_Delmerico.pdf"

BOARDS = (
    Board("Raspberry Pi 5 (4 GB)", hardware_encoder=False, facts=(
        Fact("video encode", "no hardware H.264 encoder; libx264 on the CPU does 1080p30 in "
             "real time on as little as 60% of one core", PI_WHITE_PAPER),
        Fact("mass", "46 g, a reseller's figure (Raspberry Pi publishes none)",
             "https://www.ldlc.com/en/product/PB00574323.html"),
        Fact("power", "3.3 W idle, 9.8 W flat out; 8 W budgeted for a CPU kept busy encoding",
             "https://www.jeffgeerling.com/blog/2024/new-2gb-pi-5-has-33-smaller-die-30-idle-power-savings/"),
    )),
    Board("Jetson Orin Nano (8 GB)", hardware_encoder=False, facts=(
        Fact("video encode", "no NVENC engine; NVIDIA's own answer is libx264 on the CPU",
             NVIDIA_SW_ENCODE),
        Fact("power", "7 to 25 W by power mode, the 25 W mode since JetPack 6.2", NVIDIA_SUPER),
        Fact("mass", "not published for the module; it needs a carrier board and a heatsink "
             "besides", NVIDIA_SUPER),
    )),
)  # fmt: skip

JOBS = (
    Job("the live video", "the laptop only sees what the drone sends",
        "720p at the 1 to 7 Mbps HaLow holds: a CPU encode on either board", PI_WHITE_PAPER),
    Job("GPS-free flight (#24)", "it has to work when the link drops",
        "visual-inertial odometry; the published benchmark ran the main open-source pipelines on "
        "embedded ARM boards a generation older than the Pi 5's", VIO_BENCHMARK),
    Job("photos for mapping", "full-resolution stills, sent when the link allows",
        "the camera and storage, no real compute", "decisions.md, under the link"),
)  # fmt: skip


@dataclass(frozen=True)
class Verdict:
    pick: str
    why: str


def verdict() -> Verdict:
    return Verdict(
        pick="Raspberry Pi 5 (4 GB)",
        why=("The jobs that need a GPU (the LLM, the object detector) run on the laptop, and "
             "neither board has a hardware video encoder, so the encode costs CPU on both. What "
             "stays on board is a CPU job plus visual-inertial odometry, which runs on older "
             "ARM boards than the Pi 5. The Orin Nano would add watts the battery pays for "
             "without a job to spend its GPU on."),
    )  # fmt: skip
