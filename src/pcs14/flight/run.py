"""Flying a scenario: Gazebo, PX4 and a scenario script, together.

This runs inside WSL2 Ubuntu 24.04 on the PC (or native Ubuntu), where scripts/setup-ubuntu.sh
puts the tools. One run:

1. Gazebo's server, headless, on our generated world, with Gazebo's search paths pointing at our
   generated models, PX4's own Gazebo plugins and our drag plugin
2. PX4 v1.17.0 in Gazebo's standalone mode, unmodified: its stock x500 airframe (4001) with the
   combination's parameters loaded over it at boot (PX4 reads PX4_PARAM_* from its environment),
   spawning the combination's model itself
3. a small relay between PX4 and MAVSDK, so a scenario can cut the uplink: PX4 then hears
   nothing from the ground, exactly as when the radio drops, while the script still sees
   everything PX4 sends
4. MAVSDK, which flies the scenario script on PX4's clock, so a run keeps time at any speed

Each run gets its own folder in the work folder (in the Ubuntu home, not /mnt/c, because WSL
reads Windows files slowly) holding Gazebo's and PX4's output and PX4's log. The log is copied
to outputs/flight-sim/logs/ when the run ends, and never committed.

Several runs can go at once: each gets its own PX4 instance, which moves its ports, and its own
Gazebo partition.
"""

import asyncio
import contextlib
import importlib
import os
import re
import shutil
import signal
import sys
import threading
import time
from dataclasses import dataclass, field
from pathlib import Path

from pcs14.flight.scenarios import Aborted

WORLD = "pcs14"
AIRFRAME = 4001  # PX4's x500, which the generated parameters go over
API_PORT = 14540  # where PX4's API link sends, plus the instance; the relay sits here
SDK_PORT = 14640  # where MAVSDK listens, behind the relay
GRPC_PORT = 50051  # MAVSDK's own server, plus the instance
# what every run sets on top of the model's parameters
RUN_PARAMS = {
    "SDLOG_MODE": 2,  # log from boot until shutdown, so what happens after a disarm is in it
}
CONNECT_S = 90.0  # wall seconds for PX4 to boot, spawn the model and talk
# s of real time the offboard setpoints may pause before PX4 calls them lost. MAVSDK resends
# them at 20 Hz, but under load the runner's own Python can fall behind for a moment, and that
# isn't what any scenario tests (a real dropped radio is the lost-link scenario's job, through
# the relay). PX4's own default, scaled by the sim speed, is 1 s of real time
OFFBOARD_LOSS_S = 3.0
STALL_S = 30.0  # wall seconds PX4's clock may stand still before the run counts as hung
FIRMWARES = ("px4", "mine")  # what flies: PX4 v1.17.0, or my own (firmware/, step 5)
# what my firmware's scenario runs set on top: the scenarios compare it with PX4, which doesn't
# have my parachute rule (no autonomous flight above 30 m without P), so the rule is off for
# them; it has its own test (firmware/core/tests/test_limits.cpp)
MINE_RUN_PARAMS = {"PCS14_CHUTE_RULE": 0}


def mine_params(params: dict) -> dict:
    """A run's parameters for my firmware: the run's own on top, then MINE_RUN_PARAMS where the
    scenario didn't set them itself (the chute rule scenario switches the rule back on)."""
    return {**params, **RUN_PARAMS,
            **{k: v for k, v in MINE_RUN_PARAMS.items() if k not in params}}  # fmt: skip


GZ_SYSTEM_PYTHON = "/usr/lib/python3/dist-packages"  # where Ubuntu's python3-gz-* packages go
GZ_MSGS = "gz.msgs10"  # Harmonic's message package
CONNECT_TOPIC_S = 2.0  # wall seconds a new publisher waits for Gazebo to hear about it


class SimError(RuntimeError):
    """The sim itself failed (as opposed to the drone failing a check)."""


@dataclass(frozen=True)
class Toolchain:
    px4: Path  # PX4's source, at v1.17.0
    plugin: Path  # our drag plugin's build folder

    @property
    def build(self) -> Path:
        return self.px4 / "build" / "px4_sitl_default"

    @property
    def binary(self) -> Path:
        return self.build / "bin" / "px4"

    @property
    def gz_models(self) -> Path:
        return self.px4 / "Tools" / "simulation" / "gz" / "models"

    @property
    def gz_plugins(self) -> Path:
        return self.build / "src" / "modules" / "simulation" / "gz_plugins"

    @property
    def server_config(self) -> Path:
        return self.px4 / "src" / "modules" / "simulation" / "gz_bridge" / "server.config"

    def missing(self) -> list[str]:
        """What's missing for a run, in words; empty when everything's there."""
        out = []
        if shutil.which("gz") is None:
            out.append("Gazebo's gz isn't on the PATH")
        if not self.binary.exists():
            out.append(f"PX4 isn't built for the simulator (no {self.binary.as_posix()})")
        if not (self.plugin / "libpcs14-drag.so").exists():
            out.append(f"the drag plugin isn't built (no libpcs14-drag.so in {self.plugin})")
        try:
            import mavsdk  # noqa: F401
            import pyulog  # noqa: F401
        except ImportError:
            out.append("MAVSDK-Python and pyulog aren't installed (pip install -e .[flight])")
        return out


def toolchain(environ=None) -> Toolchain:
    """Where scripts/setup-ubuntu.sh puts things, or wherever PX4_DIR and PLUGIN_BUILD say."""
    environ = os.environ if environ is None else environ
    home = Path(environ.get("HOME") or Path.home())
    return Toolchain(
        px4=Path(environ.get("PX4_DIR") or home / "px4" / "PX4-Autopilot"),
        plugin=Path(environ.get("PLUGIN_BUILD") or home / "build" / "pcs14_drag"),
    )


def work_folder(environ=None) -> Path:
    environ = os.environ if environ is None else environ
    home = Path(environ.get("HOME") or Path.home())
    return Path(environ.get("PCS14_FLIGHT_WORK") or home / ".cache" / "pcs14" / "flight-sim")


def _number(value) -> str:
    if isinstance(value, bool):
        return str(int(value))
    if isinstance(value, int):
        return str(value)
    return f"{value:.9g}"


def _search_path(*parts, existing: str | None = None) -> str:
    items = [Path(p).as_posix() for p in parts]
    if existing:
        items.append(existing)
    return ":".join(items)


def gz_environment(tools: Toolchain, models, worlds, partition: str, environ=None) -> dict:
    """Gazebo's environment: our models and world first, then PX4's models; PX4's plugins and
    our drag plugin; PX4's server config (the systems every PX4 world needs); and a partition
    of its own, so runs side by side don't hear each other."""
    environ = dict(os.environ if environ is None else environ)
    environ["GZ_SIM_RESOURCE_PATH"] = _search_path(
        models, worlds, tools.gz_models, existing=environ.get("GZ_SIM_RESOURCE_PATH")
    )
    environ["GZ_SIM_SYSTEM_PLUGIN_PATH"] = _search_path(
        tools.gz_plugins, tools.plugin, existing=environ.get("GZ_SIM_SYSTEM_PLUGIN_PATH")
    )
    environ["GZ_SIM_SERVER_CONFIG_PATH"] = Path(tools.server_config).as_posix()
    environ["GZ_PARTITION"] = partition
    environ["GZ_IP"] = "127.0.0.1"  # keep Gazebo's discovery on this machine
    return environ


def px4_environment(model_name: str, params: dict, models, speed: float = 1.0, base=None):
    """PX4's environment for one run: standalone mode, the x500 airframe, our model (PX4 spawns
    it), and every parameter as PX4_PARAM_<name>, which PX4's startup sets over the airframe's
    defaults."""
    environ = dict(base or {})
    environ.update(
        {
            "PX4_GZ_STANDALONE": "1",
            "PX4_SYS_AUTOSTART": str(AIRFRAME),
            "PX4_SIM_MODEL": f"gz_{model_name}",
            "PX4_GZ_WORLD": WORLD,
            "PX4_GZ_MODELS": Path(models).as_posix(),
            "HEADLESS": "1",
        }
    )
    if speed != 1:
        environ["PX4_SIM_SPEED_FACTOR"] = _number(float(speed))
    for name, value in {**params, **RUN_PARAMS}.items():
        environ[f"PX4_PARAM_{name}"] = _number(value)
    return environ


def params_text(params: dict) -> str:
    """The parameters for my firmware's sim layer: "NAME value" lines, an int32 written
    without a decimal point and a float with one, the way pcs14_sitl tells them apart."""
    lines = []
    for name, value in sorted(params.items()):
        text = str(int(value)) if isinstance(value, (bool, int)) else repr(float(value))
        lines.append(f"{name} {text}")
    return "\n".join(lines) + "\n"


def sitl_command(binary, entity: str, airframe, instance: int, params, monitor=False):
    """My firmware's sim layer, flying Gazebo's `entity`, on PX4's ports for `instance`; with
    `monitor`, through the safety monitor."""
    return [
        Path(binary).as_posix(), "--world", WORLD, "--model", entity,
        "--airframe", Path(airframe).as_posix(), "--instance", str(instance),
        "--params", Path(params).as_posix(), "--log", "log/sitl.ulg",
    ] + (["--monitor"] if monitor else [])  # fmt: skip


def monitor_command(binary, entity: str, live: bool = False, chute: bool = False) -> list[str]:
    """The safety monitor in the sim, between my firmware and `entity`'s motors; with `chute`
    (P is fitted) it can fire the chute on the pilot's switch."""
    return (
        [Path(binary).as_posix(), "--world", WORLD, "--model", entity]
        + (["--live"] if live else [])
        + (["--chute"] if chute else [])
    )


# what the monitor's log says that a run's record keeps
MONITOR_LINES = ("cut ", "trigger ", "chute ")


def gz_command(world, verbose: int = 2) -> list[str]:
    """Gazebo's server, headless, running from the start."""
    return ["gz", "sim", "-s", "-r", f"--verbose={verbose}", Path(world).as_posix()]


def px4_command(tools: Toolchain, workdir, instance: int = 0) -> list[str]:
    """PX4 as a daemon (no shell), in its own working folder."""
    return [
        tools.binary.as_posix(),
        "-i",
        str(instance),
        "-d",
        (tools.build / "etc").as_posix(),
        "-w",
        Path(workdir).as_posix(),
    ]


def model_name(instance: int, name: str) -> str:
    """What PX4 calls the model it spawns."""
    return f"{name}_{instance}"


def gz_message(message_type: str) -> tuple[str, str]:
    """The Python module and class for a Gazebo message type: gz.msgs.EntityFactory is
    EntityFactory in gz.msgs10.entity_factory_pb2."""
    name = message_type.rsplit(".", 1)[-1]
    return f"{GZ_MSGS}.{re.sub(r'(?<!^)(?<!_)(?=[A-Z])', '_', name).lower()}_pb2", name


def gz_bindings():
    """Gazebo's own Python bindings for its transport, or None where they aren't installed.
    Ubuntu's packages put them in the system Python's folder, outside the venv, so that folder
    goes at the end of the search path, behind everything the venv has."""
    try:
        return importlib.import_module("gz.transport13")
    except ImportError:
        if GZ_SYSTEM_PYTHON in sys.path or not Path(GZ_SYSTEM_PYTHON).is_dir():
            return None
        sys.path.append(GZ_SYSTEM_PYTHON)
    try:
        return importlib.import_module("gz.transport13")
    except ImportError:
        return None


def _text_format():
    from google.protobuf import text_format  # Gazebo's bindings bring it

    return text_format


class GzTopics:
    """Publishes on Gazebo topics, asks its services and follows the models' poses from inside
    the runner, through Gazebo's Python bindings.

    The first version started gz's command line for every message: about 0.9 s and a quarter
    of a CPU second each (measured 2026-10-20), against 0.04 s here. Two runs at 4x already
    load the PC to about 12 of its 16 threads, and a spike on top can starve PX4 of its sensors
    for tens of milliseconds of sim time."""

    def __init__(self, transport, partition: str, parse=None, load=importlib.import_module,
                 show=None):  # fmt: skip
        os.environ["GZ_IP"] = "127.0.0.1"  # the same discovery as Gazebo's (gz_environment)
        options = transport.NodeOptions()
        options.partition = partition
        self.node = transport.Node(options)
        self._publishers: dict = {}
        self._load = load
        self._parse = parse or (lambda text, message: _text_format().Parse(text, message))
        self._show = show or (lambda m: _text_format().MessageToString(m, as_one_line=True))
        self._poses: dict = {}
        self._lock = threading.Lock()

    def _kind(self, message_type: str):
        module, name = gz_message(message_type)
        return getattr(self._load(module), name)

    def request(self, service: str, request_type: str, reply_type: str, payload: str,
                timeout_ms: int = 5000) -> str:  # fmt: skip
        """Asks a Gazebo service and returns its reply as text, the way gz's command line
        prints it (empty when nothing answered)."""
        kind = self._kind(request_type)
        message = kind()
        self._parse(payload, message)
        ok, reply = self.node.request(service, message, kind, self._kind(reply_type), timeout_ms)
        return self._show(reply) if ok else ""

    def watch_poses(self, world: str):
        """Starts following every model's pose in `world`, for pose()."""
        self.node.subscribe(self._kind("gz.msgs.Pose_V"), f"/world/{world}/pose/info",
                            self._on_poses)  # fmt: skip

    def _on_poses(self, message):
        found = {}
        for pose in message.pose:
            p, q = pose.position, pose.orientation
            found[pose.name] = ((p.x, p.y, p.z), (q.w, q.x, q.y, q.z))
        with self._lock:
            self._poses.update(found)

    def pose(self, name: str):
        """The model's latest pose, Gazebo's frame: ((x, y, z), (w, x, y, z)), or None."""
        with self._lock:
            return self._poses.get(name)

    async def ready(self, topic: str, message_type: str):
        """Advertises a topic and waits until Gazebo listens, so the first publish goes out at
        once."""
        kind = self._kind(message_type)
        publisher = self._publishers.get((topic, message_type))
        if publisher is None:
            publisher = self.node.advertise(topic, kind)
            self._publishers[(topic, message_type)] = publisher
            # a message sent before Gazebo has heard about the publisher goes nowhere
            deadline = time.monotonic() + CONNECT_TOPIC_S
            while not publisher.has_connections() and time.monotonic() < deadline:
                await asyncio.sleep(0.02)
        return publisher, kind

    async def publish(self, topic: str, message_type: str, payload: str):
        publisher, kind = await self.ready(topic, message_type)
        message = kind()
        self._parse(payload, message)
        publisher.publish(message)


class Relay:
    """A UDP relay between PX4's API link and MAVSDK. Everything PX4 sends goes through; what
    MAVSDK sends goes through unless the uplink is cut."""

    def __init__(self, px4_port: int, sdk_port: int, host: str = "127.0.0.1"):
        self.host, self.px4_port, self.sdk_port = host, px4_port, sdk_port
        self.cut = False
        self.dropped = 0
        self.px4_address = None
        self._px4 = self._sdk = None

    async def start(self):
        loop = asyncio.get_running_loop()
        relay = self

        class FromPx4(asyncio.DatagramProtocol):
            def datagram_received(self, data, addr):
                relay.px4_address = addr
                relay._sdk.sendto(data, (relay.host, relay.sdk_port))

        class FromSdk(asyncio.DatagramProtocol):
            def datagram_received(self, data, addr):
                if relay.cut or relay.px4_address is None:
                    relay.dropped += 1
                else:
                    relay._px4.sendto(data, relay.px4_address)

        self._sdk, _ = await loop.create_datagram_endpoint(FromSdk, local_addr=(self.host, 0))
        self._px4, _ = await loop.create_datagram_endpoint(
            FromPx4, local_addr=(self.host, self.px4_port)
        )
        return self

    def close(self):
        for transport in (self._px4, self._sdk):
            if transport is not None:
                transport.close()


GCS_PORT = 14550  # where my firmware sends its ground station MAVLink, plus the instance


@dataclass
class LinkSecond:
    t: int  # s of the sim's clock
    distance_m: float  # the drone's, from home, as the second began
    sent: int = 0
    delivered: int = 0


class HalowLink:
    """The ground station's end of the drone's HaLow link, in the sim. It listens where my
    firmware sends its ground station MAVLink (14550 + instance), drops each datagram with the
    HaLow model's packet loss at the drone's distance (`loss`), and counts what was sent and what
    got through, a second of the sim's clock at a time. Nothing goes back up: the laptop's end
    is only listening."""

    def __init__(self, port: int, loss, now, distance, seed: int = 1, host: str = "127.0.0.1"):
        import random

        self.port, self.host = port, host
        self.loss, self.now, self.distance = loss, now, distance
        self.seconds: list[LinkSecond] = []
        self._random = random.Random(seed)
        self._transport = None

    async def start(self):
        link = self

        class Listen(asyncio.DatagramProtocol):
            def datagram_received(self, data, addr):
                link._count(link._random.random() >= link.loss())

        loop = asyncio.get_running_loop()
        self._transport, _ = await loop.create_datagram_endpoint(
            Listen, local_addr=(self.host, self.port))  # fmt: skip
        self.port = self._transport.get_extra_info("sockname")[1]
        return self

    def _count(self, delivered: bool):
        t = int(self.now() or 0)
        if not self.seconds or self.seconds[-1].t != t:
            self.seconds.append(LinkSecond(t, float(self.distance())))
        self.seconds[-1].sent += 1
        self.seconds[-1].delivered += int(delivered)

    def close(self):
        if self._transport is not None:
            self._transport.close()


class CameraRecorder:
    """Saves a Gazebo camera's frames as PNGs, every `every`th one, with each one's sim time in
    frames.txt: what the live video and the mapping runs start from."""

    def __init__(self, topics, topic: str, folder: Path, every: int = 3):
        self.folder = Path(folder)
        self.folder.mkdir(parents=True, exist_ok=True)
        self.every, self.seen, self.saved = every, 0, []
        self._lock = threading.Lock()
        topics.node.subscribe(topics._kind("gz.msgs.Image"), topic, self._on_image)

    def _on_image(self, message):
        import numpy as np
        from PIL import Image

        with self._lock:
            self.seen += 1
            if (self.seen - 1) % self.every:
                return
            t = message.header.stamp.sec + message.header.stamp.nsec * 1e-9
            k = len(self.saved)
        pixels = np.frombuffer(message.data, dtype=np.uint8)
        frame = pixels.reshape(message.height, message.width, -1)[:, :, :3]
        Image.fromarray(frame).save(self.folder / f"frame-{k:04d}.png")
        with self._lock:
            self.saved.append(t)

    def close(self):
        with self._lock:
            times = list(self.saved)
        (self.folder / "frames.txt").write_text("".join(f"{t:.3f}\n" for t in times), "utf-8")


class Clock:
    """PX4's clock, s since it booted, from the IMU timestamps MAVSDK passes on. In the sim
    that's Gazebo's time, so the scripts keep time at any speed. If it stands still for
    STALL_S of real time, the sim has hung."""

    def __init__(self, stall_s: float = STALL_S):
        self.now: float | None = None
        self.stall_s = stall_s
        self._moved = time.monotonic()

    async def follow(self, timestamps_us):
        async for stamp in timestamps_us:
            now = stamp / 1e6
            if self.now is None or now > self.now:
                self._moved = time.monotonic()
            self.now = now

    def _check(self):
        if time.monotonic() - self._moved > self.stall_s:
            raise SimError(f"PX4's clock stopped for {self.stall_s:g} s of real time")

    async def started(self):
        while self.now is None:
            self._check()
            await asyncio.sleep(0.01)

    async def sleep(self, seconds: float):
        await self.started()
        end = self.now + seconds
        while self.now < end:
            self._check()
            await asyncio.sleep(0.005)

    async def until(self, condition, timeout: float, poll: float = 0.01) -> bool:
        """Waits for `condition()` to come true, for up to `timeout` s on PX4's clock."""
        await self.started()
        end = self.now + timeout
        while self.now < end:
            if condition():
                return True
            self._check()
            await asyncio.sleep(poll)
        return bool(condition())


@dataclass
class State:
    """The latest of what PX4 reports, for the scripts' conditions. Positions are PX4's own
    estimate, north-east-down from home; the grades use Gazebo's ground truth instead."""

    armed: bool = False
    in_air: bool = False
    mode: str = ""
    north: float = 0.0
    east: float = 0.0
    down: float = 0.0
    speed: float = 0.0  # m/s, sideways
    heading: float = 0.0  # degrees from north, clockwise, as of the last heading() read
    battery: float | None = None  # PX4's remaining share, 1 is full
    peak: float = 0.0  # m: the highest it has been, by PX4's estimate

    @property
    def height(self) -> float:
        return -self.down


async def _follow_state(drone, state: State):
    async def armed():
        async for value in drone.telemetry.armed():
            state.armed = value

    async def in_air():
        async for value in drone.telemetry.in_air():
            state.in_air = value

    async def mode():
        async for value in drone.telemetry.flight_mode():
            state.mode = str(value)

    async def position():
        async for value in drone.telemetry.position_velocity_ned():
            p, v = value.position, value.velocity
            state.north, state.east, state.down = p.north_m, p.east_m, p.down_m
            state.peak = max(state.peak, -p.down_m)
            state.speed = (v.north_m_s**2 + v.east_m_s**2) ** 0.5

    async def battery():
        async for value in drone.telemetry.battery():
            state.battery = value.remaining_percent / 100

    # no heading stream: the scripts read it when they need it (read_heading), which keeps
    # the telemetry the runner's Python has to keep up with down
    await asyncio.gather(armed(), in_air(), mode(), position(), battery())


async def read_heading(drone, state: State) -> float:
    """degrees: PX4's heading right now, into `state` too."""
    value = await first(drone.telemetry.heading(), lambda _: True)
    state.heading = value.heading_deg
    return state.heading


async def first(stream, condition):
    """The first item of a MAVSDK stream that meets `condition`, closing the stream after:
    an abandoned stream keeps MAVSDK queueing messages nobody reads."""
    try:
        async for item in stream:
            if condition(item):
                return item
    finally:
        await stream.aclose()


async def _imu_stamps(drone):
    async for imu in drone.telemetry.imu():
        yield imu.timestamp_us


@dataclass
class RunResult:
    model: str
    scenario: str
    folder: Path
    log: Path | None = None  # PX4's log, copied out of the work folder
    marks: list = field(default_factory=list)  # (s on PX4's clock, name), from the script
    notes: dict = field(default_factory=dict)  # whatever the script wants the grader to know
    error: str | None = None  # the sim failing, not the drone
    aborted: str | None = None  # the drone not doing what the script needed
    wall_s: float = 0.0
    speed: float = 1.0  # the sim's speed against real time


class Session:
    """One run's Gazebo, PX4, relay and MAVSDK. The scenario script gets this: `drone` is
    MAVSDK's System, `clock` and `state` follow PX4, `mark(name)` notes an event for the
    grader, `relay.cut` drops the uplink, and `gz_publish` sends to Gazebo's topics (the wind,
    the chute, the payload)."""

    def __init__(
        self,
        tools: Toolchain,
        model: str,
        params: dict,
        exports: Path,
        scenario: str,
        instance: int = 0,
        speed: float = 1.0,
        work: Path | None = None,
        firmware: str = "px4",
        monitor: bool = True,
    ):
        if firmware not in FIRMWARES:
            raise ValueError(f"no firmware called {firmware}: there's {', '.join(FIRMWARES)}")
        self.firmware = firmware
        self.monitor = monitor and firmware == "mine"  # the safety monitor, with my firmware
        self.tools, self.model, self.params = tools, model, params
        self.exports, self.scenario = Path(exports), scenario
        self.instance, self.speed = instance, speed
        self.folder = (work or work_folder()) / f"{model}-{scenario}"
        self.partition = f"pcs14_{os.getpid()}_{instance}"
        self.result = RunResult(model, scenario, self.folder, speed=speed)
        self.clock = Clock()
        self.state = State()
        self.relay = Relay(API_PORT + instance, SDK_PORT + instance)
        self.drone = None
        self.context = None  # pcs14.flight.scenarios.Context, for the script
        self.world_file = WORLD  # the world's file: pcs14, or pcs14-fine for a finer step
        self.camera = False  # V's camera on the model, for the scenarios that look
        self._processes: list = []
        self._tasks: list = []
        self._outputs: list = []
        self.gz_env: dict = {}
        self._topics: GzTopics | None = None

    @property
    def entity(self) -> str:
        """The model's name in Gazebo's world."""
        return model_name(self.instance, self.model)

    def mark(self, name: str):
        self.result.marks.append((self.clock.now, name))

    async def _spawn(self, command, name: str, **kwargs):
        out = open(self.folder / f"{name}.log", "wb")  # noqa: SIM115 (closed in stop)
        self._outputs.append(out)
        kwargs.setdefault("stdin", asyncio.subprocess.DEVNULL)
        kwargs.setdefault("stdout", out)
        process = await asyncio.create_subprocess_exec(
            *command,
            stderr=asyncio.subprocess.STDOUT if kwargs["stdout"] is out else out,
            start_new_session=True,
            **kwargs,
        )
        self._processes.append((name, process))
        return process

    def gz(self) -> GzTopics | None:
        """Gazebo's topics and services in-process, or None without the Python bindings."""
        if self._topics is None and (transport := gz_bindings()) is not None:
            self._topics = GzTopics(transport, self.partition)
            self._topics.watch_poses(WORLD)
        return self._topics

    def true_pose(self, name: str):
        """A model's pose as Gazebo has it: ((x, y, z), (w, x, y, z)) in Gazebo's frame (x
        east, y north, z up), or None before one has come in or without the bindings."""
        topics = self.gz()
        return topics.pose(name) if topics is not None else None

    async def gz_publish(self, topic: str, message_type: str, payload: str):
        """Publishes one message on a Gazebo topic: through Gazebo's Python bindings when
        they're installed (GzTopics), otherwise through gz's own command line."""
        if (topics := self.gz()) is not None:
            await topics.publish(topic, message_type, payload)
            return
        process = await asyncio.create_subprocess_exec(
            "gz", "topic", "-t", topic, "-m", message_type, "-p", payload,
            env=self.gz_env,
            stdout=asyncio.subprocess.DEVNULL,
            stderr=asyncio.subprocess.DEVNULL,
        )  # fmt: skip
        await process.wait()

    async def gz_service(self, service: str, request_type: str, reply_type: str, request: str,
                         fast: bool = False):  # fmt: skip
        """Asks a Gazebo service through gz's command line, or with `fast` through the Python
        bindings (milliseconds against about a second)."""
        if fast and (topics := self.gz()) is not None:
            return topics.request(service, request_type, reply_type, request)
        process = await asyncio.create_subprocess_exec(
            "gz", "service", "-s", service, "--reqtype", request_type, "--reptype", reply_type,
            "--timeout", "5000", "--req", request,
            env=self.gz_env,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.STDOUT,
        )  # fmt: skip
        out, _ = await process.communicate()
        return out.decode(errors="replace")

    async def wait_for_world(self, attempts: int = 60):
        """Waits until Gazebo's world answers, the way PX4's own startup does."""
        for _ in range(attempts):
            process = await asyncio.create_subprocess_exec(
                "gz", "service", "-i", "--service", f"/world/{WORLD}/scene/info",
                env=self.gz_env,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.STDOUT,
            )  # fmt: skip
            out, _ = await process.communicate()
            if b"Service providers" in out:
                return
            await asyncio.sleep(1.0)
        raise SimError("Gazebo's world never came up; see gz.log")

    def _model_sdf(self, home: Path) -> Path:
        """The model's SDF, or with the camera on it, a copy in the run's folder (its meshes
        are model:// paths, so they still resolve)."""
        if not self.camera:
            return home / "model.sdf"
        from pcs14.flight.generate import with_camera

        copy = self.folder / "model-camera.sdf"
        copy.write_text(with_camera((home / "model.sdf").read_text(encoding="utf-8")), "utf-8")
        return copy

    def record_camera(self, folder: Path, every: int = 3) -> "CameraRecorder":
        """Starts saving every `every`th frame of the model's camera into `folder`."""
        topic = f"/world/{WORLD}/model/{self.entity}/link/base_link/sensor/camera/image"
        return CameraRecorder(self.gz(), topic, folder, every)

    async def spawn(self, sdf_file, name: str, position=(0.0, 0.0, 0.0)):
        """Puts a model from an SDF file into the world (Gazebo's own frame: x east, y north,
        z up)."""
        x, y, z = position
        reply = await self.gz_service(
            f"/world/{WORLD}/create", "gz.msgs.EntityFactory", "gz.msgs.Boolean",
            f'sdf_filename: "{Path(sdf_file).as_posix()}", name: "{name}", '
            f"pose: {{position: {{x: {x}, y: {y}, z: {z}}}}}",
        )  # fmt: skip
        if "true" not in reply:
            raise SimError(f"Gazebo wouldn't spawn {name}: {reply.strip()}")

    async def spawn_sdf(self, sdf: str, name: str, position=(0.0, 0.0, 0.0)):
        """Puts a model written out as SDF into the world, Gazebo's frame like spawn."""
        x, y, z = position
        reply = await self.gz_service(
            f"/world/{WORLD}/create", "gz.msgs.EntityFactory", "gz.msgs.Boolean",
            f"sdf: '{sdf}', name: \"{name}\", pose: {{position: {{x: {x}, y: {y}, z: {z}}}}}",
        )  # fmt: skip
        if "true" not in reply:
            raise SimError(f"Gazebo wouldn't spawn {name}: {reply.strip()}")

    async def start_gazebo(self):
        """Gazebo's server, headless, in a fresh run folder: the first half of start, and all
        my own firmware needs before its model goes in (pcs14.flight.firmware)."""
        if self.folder.exists():
            shutil.rmtree(self.folder)
        self.folder.mkdir(parents=True)
        models, worlds = self.exports / "models", self.exports / "worlds"
        self.gz_env = gz_environment(self.tools, models, worlds, self.partition)
        await self._spawn(gz_command(worlds / f"{self.world_file}.sdf"), "gz", env=self.gz_env)

    async def start(self, before_px4=None):
        from mavsdk import System

        await self.start_gazebo()
        models = self.exports / "models"
        if before_px4 is not None:
            await self.wait_for_world()
            await before_px4(self)
        if self.firmware == "mine":
            await self._start_mine(models, world_ready=before_px4 is not None)
        else:
            environ = px4_environment(self.model, self.params, models, self.speed, self.gz_env)
            await self._spawn(
                px4_command(self.tools, self.folder, self.instance), "px4", env=environ,
                cwd=self.folder,
            )  # fmt: skip
        await self.relay.start()
        self.drone = System(port=GRPC_PORT + self.instance)
        await self.drone.connect(system_address=f"udpin://127.0.0.1:{SDK_PORT + self.instance}")

        async def connected():
            await first(self.drone.core.connection_state(), lambda status: status.is_connected)

        try:
            await asyncio.wait_for(connected(), CONNECT_S)
        except TimeoutError as e:
            raise SimError(f"PX4 didn't connect within {CONNECT_S:g} s; see px4.log") from e
        await self.drone.telemetry.set_rate_imu(50.0)
        await self.drone.telemetry.set_rate_position_velocity_ned(10.0)
        await self.drone.telemetry.set_rate_battery(1.0)
        self._tasks.append(asyncio.create_task(self.clock.follow(_imu_stamps(self.drone))))
        self._tasks.append(asyncio.create_task(_follow_state(self.drone, self.state)))
        await asyncio.wait_for(self.clock.started(), CONNECT_S)

        async def healthy():
            await first(
                self.drone.telemetry.health(),
                lambda h: h.is_global_position_ok and h.is_home_position_ok,
            )

        if not _finished(await self.within(healthy(), 120.0)):
            raise SimError("PX4 never got a position fix and a home position")
        # PX4's startup scales this by the sim speed itself, after reading our parameters, so
        # it's set here, once it's up
        await self.drone.param.set_param_float("COM_OF_LOSS_T", OFFBOARD_LOSS_S * self.speed)
        return self

    async def _start_mine(self, models: Path, world_ready: bool):
        """My firmware in PX4's place (step 5): the runner spawns the model the way PX4's
        startup does, sets Gazebo's speed the same way, and hands the parameters over in a
        file, PX4's names and all. pcs14_sitl then speaks MAVLink on PX4's ports for the same
        instance, so the relay and MAVSDK can't tell the difference."""
        import json

        from pcs14.flight.firmware import sitl_binary

        binary = sitl_binary()
        if not binary.exists():
            raise SimError(f"no pcs14_sitl at {binary}; run scripts/build-firmware.sh")
        home = (models / self.model).resolve()  # it runs in the run's own folder
        info = json.loads((home / "model.json").read_text())
        if not world_ready:
            await self.wait_for_world()
        await self.spawn(self._model_sdf(home), self.entity, (0.0, 0.0, info["lift_off_m"]))
        if self.speed != 1:
            await self.gz_service(
                f"/world/{WORLD}/set_physics", "gz.msgs.Physics", "gz.msgs.Boolean",
                f"real_time_factor: {_number(float(self.speed))}",
            )  # fmt: skip
        params = self.folder / "params.txt"
        values = mine_params(self.params)
        params.write_text(params_text(values), encoding="utf-8")
        if self.monitor:
            watcher = binary.parent / "pcs14_monitor_sitl"
            if not watcher.exists():
                raise SimError(f"no pcs14_monitor_sitl at {watcher}; run scripts/build-firmware.sh")
            await self._spawn(monitor_command(watcher, self.entity, chute="chute" in info),
                              "monitor", env=self.gz_env, cwd=self.folder)  # fmt: skip
        process = await self._spawn(
            sitl_command(binary, self.entity, home / "firmware.txt", self.instance, params,
                         self.monitor),
            "sitl", env=self.gz_env, cwd=self.folder,
        )  # fmt: skip
        # a bridge that can't start (a missing file, a bad parameter) says so and leaves at once
        with contextlib.suppress(TimeoutError):
            await asyncio.wait_for(process.wait(), 1.0)
        if process.returncode is not None:
            log = (self.folder / "sitl.log").read_text(errors="replace").strip()
            raise SimError(f"pcs14_sitl stopped at start: {log[-300:]}")

    async def within(self, awaitable, sim_seconds: float) -> asyncio.Task:
        """Runs `awaitable` for up to `sim_seconds` on PX4's clock, and returns its task:
        cancelled if it ran out of time."""
        task = asyncio.create_task(awaitable)
        try:
            await self.clock.until(task.done, sim_seconds)
        finally:
            if not task.done():
                task.cancel()
                with contextlib.suppress(BaseException):
                    await task
        return task

    async def stop(self):
        for task in self._tasks:
            task.cancel()
        for task in self._tasks:
            with contextlib.suppress(BaseException):
                await task
        if self.drone is not None:
            stop = getattr(self.drone, "_stop_mavsdk_server", None)
            if stop is not None:
                with contextlib.suppress(Exception):
                    stop()
        self.relay.close()
        self._topics = None  # its node goes, and with it the publishers
        # PX4 first, so its log closes cleanly, then Gazebo
        for name, process in sorted(self._processes, key=lambda p: p[0] != "px4"):
            await _end(process, 20.0 if name == "px4" else 10.0)
        for out in self._outputs:
            out.close()
        monitor_log = self.folder / "monitor.log"
        if monitor_log.exists():
            said = monitor_log.read_text(errors="replace").splitlines()
            self.result.notes["monitor"] = [s for s in said if s.startswith(MONITOR_LINES)]
        gz_log = self.folder / "gz.log"
        if gz_log.exists():
            self.result.marks += gz_marks(gz_log.read_text(errors="replace"))
        self.result.log = self._collect_log()

    def _collect_log(self) -> Path | None:
        logs = sorted(self.folder.glob("log/**/*.ulg"), key=lambda p: p.stat().st_mtime)
        if not logs:
            return None
        target = self.exports / "logs" / f"{self.model}-{self.scenario}.ulg"
        target.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(logs[-1], target)
        return target


GZ_MARKS = {"chute fired": re.compile(r"\[pcs14-drag\] chute fired at ([0-9.eE+-]+)")}


def gz_marks(text: str) -> list[tuple[float, str]]:
    """The events our Gazebo plugins print, with their sim times: Gazebo's clock is PX4's, so
    they line up with PX4's log."""
    out = []
    for name, pattern in GZ_MARKS.items():
        out += [(float(m.group(1)), name) for m in pattern.finditer(text)]
    return out


async def _end(process, grace_s: float):
    """SIGINT to the process's group, then SIGKILL if it hasn't gone after `grace_s`."""
    if process.returncode is not None:
        return
    with contextlib.suppress(ProcessLookupError):
        os.killpg(process.pid, signal.SIGINT)
    try:
        await asyncio.wait_for(process.wait(), grace_s)
    except TimeoutError:
        with contextlib.suppress(ProcessLookupError):
            os.killpg(process.pid, signal.SIGKILL)
        await process.wait()


def _finished(task: asyncio.Task) -> bool:
    return not task.cancelled() and task.exception() is None


async def fly(session: Session, script, budget_s: float, before_px4=None) -> RunResult:
    """Starts the sim, flies `script(session)` with `budget_s` s of PX4's clock to finish, and
    stops it all, whatever happens. `before_px4(session)` sets up the world first."""
    began = time.monotonic()
    try:
        await session.start(before_px4)
        task = await session.within(script(session), budget_s)
        e = None if task.cancelled() else task.exception()
        if task.cancelled():
            session.result.aborted = f"it didn't finish within {budget_s:g} s of sim time"
        elif isinstance(e, Aborted):
            session.result.aborted = str(e)
        elif e is not None and type(e).__module__.startswith("mavsdk"):
            # PX4 refused something the script asked for: the drone's answer, not the sim's
            session.result.aborted = f"PX4 refused: {type(e).__name__}: {e}"
        elif isinstance(e, SimError):
            session.result.error = str(e)
        elif e is not None:
            session.result.error = f"the script failed: {type(e).__name__}: {e}"
    except SimError as e:
        session.result.error = str(e)
    except Exception as e:  # anything else from starting the sim: record it, keep the batch going
        session.result.error = f"the sim failed to start: {type(e).__name__}: {e}"
    finally:
        await session.stop()
        session.result.wall_s = time.monotonic() - began
    return session.result
