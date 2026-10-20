"""Flying my own firmware in the flight sim (step 5).

The sim layer, firmware/sitl's pcs14_sitl, takes PX4's place. Gazebo runs exactly as it does
for PX4; the runner spawns the model the way PX4's startup would; pcs14_sitl reads the model's
own sensors and drives its motors. Until it speaks MAVLink (step 5, task 6) it takes its
commands one per line on stdin, and Gazebo's ground truth, read here through Gazebo's Python
bindings, says how it flew.
"""

import asyncio
import json
import math
import os
import threading
from dataclasses import dataclass
from pathlib import Path

from pcs14.flight.run import WORLD, Session, SimError, gz_bindings

READY_S = 60.0  # wall seconds for pcs14_sitl to hear its first IMU sample


def sitl_binary(environ=None) -> Path:
    """Where pcs14_sitl is: $PCS14_SITL, or the release build in the Ubuntu home that
    scripts/build-firmware.sh makes."""
    environ = os.environ if environ is None else environ
    if environ.get("PCS14_SITL"):
        return Path(environ["PCS14_SITL"])
    return Path(environ.get("HOME", "~")).expanduser() / "build" / "fw-sitl" / "sitl" / "pcs14_sitl"


def hover_throttle(model_info: dict) -> float:
    """The throttle whose thrust carries the model's weight, as my firmware maps throttle to
    thrust (all four motors at their top speed is 1)."""
    top = 4 * model_info["motor_constant"] * model_info["top_rot_velocity"] ** 2
    return model_info["mass_kg"] * 9.80665 / top


def tilt_deg(w: float, x: float, y: float, z: float) -> float:
    """Degrees between the body's up and the world's, from a unit quaternion."""
    c = 1 - 2 * (x * x + y * y)
    return math.degrees(math.acos(max(-1.0, min(1.0, c))))


class GroundTruth:
    """The model's pose as Gazebo has it, from the world's pose topic (what PX4's bridge logs
    as ground truth too)."""

    def __init__(self, transport, partition: str, entity: str, world: str = WORLD):
        from gz.msgs10.pose_v_pb2 import Pose_V

        options = transport.NodeOptions()
        options.partition = partition
        self._node = transport.Node(options)
        self._entity = entity
        self._lock = threading.Lock()
        self.t = -1.0  # s, sim time of the last pose
        self.height = 0.0  # m above the world's origin
        self.tilt = 0.0  # degrees
        self._node.subscribe(Pose_V, f"/world/{world}/pose/info", self._on_poses)

    def _on_poses(self, message):
        for pose in message.pose:
            if pose.name == self._entity:
                q = pose.orientation
                with self._lock:
                    self.t = message.header.stamp.sec + message.header.stamp.nsec * 1e-9
                    self.height = pose.position.z
                    self.tilt = tilt_deg(q.w, q.x, q.y, q.z)
                return

    def now(self) -> tuple[float, float, float]:
        with self._lock:
            return self.t, self.height, self.tilt


@dataclass
class RateCheck:
    """How rate mode flew: the worst tilt while airborne, the height at the end."""

    worst_tilt_deg: float
    end_height_m: float
    seconds: float
    lines: list  # what pcs14_sitl printed
    log: Path | None = None  # its ULog, copied to outputs/flight-sim/logs/


async def _send(process, line: str):
    process.stdin.write((line + "\n").encode())
    await process.stdin.drain()


async def _read_until(process, prefix: str, timeout: float, lines: list) -> str:
    async def read():
        while True:
            raw = await process.stdout.readline()
            if not raw:
                raise SimError(f"pcs14_sitl ended before saying {prefix!r}: {lines[-5:]}")
            line = raw.decode(errors="replace").strip()
            lines.append(line)
            if line.startswith(prefix):
                return line

    return await asyncio.wait_for(read(), timeout)


async def rate_check(tools, exports, model: str, climb_s=3.0, hold_s=10.0, instance=0):
    """Rate mode on my firmware, in Gazebo: arm, climb for `climb_s` at 15% over the hover
    throttle, then hold the hover throttle for `hold_s`, the sticks centered throughout.
    Returns a RateCheck."""
    transport = gz_bindings()
    if transport is None:
        raise SimError("Gazebo's Python bindings (python3-gz-transport13) aren't installed")
    binary = sitl_binary()
    if not binary.exists():
        raise SimError(f"no pcs14_sitl at {binary}; run scripts/build-firmware.sh")
    exports = Path(exports)
    home = exports / "models" / model
    info = json.loads((home / "model.json").read_text())
    session = Session(tools, model, {}, exports, "rate-check", instance)
    lines: list = []
    process = None
    try:
        await session.start_gazebo()
        await session.wait_for_world()
        await session.spawn(home / "model.sdf", session.entity, (0.0, 0.0, info["lift_off_m"]))
        truth = GroundTruth(transport, session.partition, session.entity)
        command = [str(binary), "--world", WORLD, "--model", session.entity,
                   "--airframe", str(home / "firmware.txt")]  # fmt: skip
        # it runs in the run's folder and logs under log/, where the runner collects PX4's
        process = await session._spawn(
            command, "sitl", env=session.gz_env, cwd=session.folder,
            stdin=asyncio.subprocess.PIPE, stdout=asyncio.subprocess.PIPE,
        )  # fmt: skip
        await _read_until(process, "ready", READY_S, lines)
        hover = hover_throttle(info)
        await _send(process, "arm")
        worst, start = 0.0, None
        for throttle, span in ((hover * 1.15, climb_s), (hover, hold_s)):
            await _send(process, f"sticks 0 0 0 {throttle:.4f}")
            began = None
            while True:
                await asyncio.sleep(0.02)
                t, height, tilt = truth.now()
                if t < 0:
                    continue
                began = t if began is None else began
                start = t if start is None else start
                if height > info["lift_off_m"] + 0.05:
                    worst = max(worst, tilt)
                if t - began >= span:
                    break
        t, height, _ = truth.now()
        await _send(process, "disarm")
        check = RateCheck(worst, height, t - start, lines)
    finally:
        if process is not None and process.returncode is None:
            try:
                await _send(process, "quit")
                await asyncio.wait_for(process.wait(), 10.0)  # so its log closes cleanly
            except (ConnectionError, RuntimeError, TimeoutError):
                pass
        await session.stop()
    check.log = session.result.log
    return check
