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
import os
import re
import shutil
import signal
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
STALL_S = 30.0  # wall seconds PX4's clock may stand still before the run counts as hung


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
    heading: float = 0.0  # degrees from north, clockwise
    battery: float | None = None  # PX4's remaining share, 1 is full

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
            state.speed = (v.north_m_s**2 + v.east_m_s**2) ** 0.5

    async def heading():
        async for value in drone.telemetry.heading():
            state.heading = value.heading_deg

    async def battery():
        async for value in drone.telemetry.battery():
            state.battery = value.remaining_percent / 100

    await asyncio.gather(armed(), in_air(), mode(), position(), heading(), battery())


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
    ):
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
        self._processes: list = []
        self._tasks: list = []
        self._outputs: list = []
        self.gz_env: dict = {}

    @property
    def entity(self) -> str:
        """The model's name in Gazebo's world."""
        return model_name(self.instance, self.model)

    def mark(self, name: str):
        self.result.marks.append((self.clock.now, name))

    async def _spawn(self, command, name: str, **kwargs):
        out = open(self.folder / f"{name}.log", "wb")  # noqa: SIM115 (closed in stop)
        self._outputs.append(out)
        process = await asyncio.create_subprocess_exec(
            *command,
            stdout=out,
            stderr=asyncio.subprocess.STDOUT,
            stdin=asyncio.subprocess.DEVNULL,
            start_new_session=True,
            **kwargs,
        )
        self._processes.append((name, process))
        return process

    async def gz_publish(self, topic: str, message_type: str, payload: str):
        """Publishes one message on a Gazebo topic, through gz's own command line."""
        process = await asyncio.create_subprocess_exec(
            "gz", "topic", "-t", topic, "-m", message_type, "-p", payload,
            env=self.gz_env,
            stdout=asyncio.subprocess.DEVNULL,
            stderr=asyncio.subprocess.DEVNULL,
        )  # fmt: skip
        await process.wait()

    async def gz_service(self, service: str, request_type: str, reply_type: str, request: str):
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

    async def start(self, before_px4=None):
        from mavsdk import System

        if self.folder.exists():
            shutil.rmtree(self.folder)
        self.folder.mkdir(parents=True)
        models, worlds = self.exports / "models", self.exports / "worlds"
        self.gz_env = gz_environment(self.tools, models, worlds, self.partition)
        await self._spawn(gz_command(worlds / f"{WORLD}.sdf"), "gz", env=self.gz_env)
        if before_px4 is not None:
            await self.wait_for_world()
            await before_px4(self)
        environ = px4_environment(self.model, self.params, models, self.speed, base=self.gz_env)
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
        await self.drone.telemetry.set_rate_position_velocity_ned(20.0)
        await self.drone.telemetry.set_rate_battery(2.0)
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
        return self

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
        # PX4 first, so its log closes cleanly, then Gazebo
        for name, process in sorted(self._processes, key=lambda p: p[0] != "px4"):
            await _end(process, 20.0 if name == "px4" else 10.0)
        for out in self._outputs:
            out.close()
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
