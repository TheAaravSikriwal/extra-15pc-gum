"""The runner's parts that don't need PX4: the environments and commands it starts Gazebo and PX4
with, the relay that can cut the uplink, and PX4's clock. The flights themselves are in
test_flight_px4.py, which only runs where PX4 is built."""

import asyncio
import socket
from pathlib import PurePosixPath

import pytest

from pcs14.flight import run

TOOLS = run.Toolchain(
    px4=PurePosixPath("/home/me/px4/PX4-Autopilot"), plugin=PurePosixPath("/home/me/build/drag")
)


def test_the_toolchain_defaults_to_where_the_setup_puts_it():
    tools = run.toolchain({"HOME": "/home/me"})
    assert tools.px4.as_posix() == "/home/me/px4/PX4-Autopilot"
    assert tools.plugin.as_posix() == "/home/me/build/pcs14_drag"
    moved = run.toolchain({"HOME": "/home/me", "PX4_DIR": "/opt/px4", "PLUGIN_BUILD": "/opt/d"})
    assert moved.px4.as_posix() == "/opt/px4" and moved.plugin.as_posix() == "/opt/d"
    assert run.work_folder({"HOME": "/home/me"}).as_posix() == "/home/me/.cache/pcs14/flight-sim"


def test_a_machine_without_px4_says_what_it_lacks(tmp_path):
    missing = run.Toolchain(px4=tmp_path / "px4", plugin=tmp_path / "drag").missing()
    assert any("PX4 isn't built" in m for m in missing)
    assert any("drag plugin" in m for m in missing)


def test_gazebo_finds_our_models_then_px4s_and_both_plugin_folders():
    env = run.gz_environment(
        TOOLS, "/w/models", "/w/worlds", "pcs14_1_0", environ={"GZ_SIM_RESOURCE_PATH": "/x"}
    )
    assert env["GZ_SIM_RESOURCE_PATH"].split(":") == [
        "/w/models",
        "/w/worlds",
        "/home/me/px4/PX4-Autopilot/Tools/simulation/gz/models",
        "/x",
    ]
    plugins = env["GZ_SIM_SYSTEM_PLUGIN_PATH"].split(":")
    assert plugins == [
        "/home/me/px4/PX4-Autopilot/build/px4_sitl_default/src/modules/simulation/gz_plugins",
        "/home/me/build/drag",
    ]
    assert env["GZ_SIM_SERVER_CONFIG_PATH"].endswith("gz_bridge/server.config")
    assert env["GZ_PARTITION"] == "pcs14_1_0" and env["GZ_IP"] == "127.0.0.1"


def test_px4_runs_standalone_on_the_x500_with_our_parameters():
    params = {"CA_ROTOR0_PX": 0.1234, "SIM_GZ_EC_MAX1": 1650, "MPC_THR_HOVER": 0.4}
    env = run.px4_environment("pcs14_base", params, "/w/models", base={"GZ_PARTITION": "p"})
    assert env["PX4_GZ_STANDALONE"] == "1"
    assert env["PX4_SYS_AUTOSTART"] == "4001"
    assert env["PX4_SIM_MODEL"] == "gz_pcs14_base"
    assert env["PX4_GZ_WORLD"] == "pcs14" and env["PX4_GZ_MODELS"] == "/w/models"
    assert env["PX4_PARAM_CA_ROTOR0_PX"] == "0.1234"
    assert env["PX4_PARAM_SIM_GZ_EC_MAX1"] == "1650"
    assert env["PX4_PARAM_SDLOG_MODE"] == "2"  # the runner's own: log until shutdown
    assert env["GZ_PARTITION"] == "p"  # PX4 talks to Gazebo, so it needs Gazebo's settings too
    assert "PX4_SIM_SPEED_FACTOR" not in env
    assert run.px4_environment("m", {}, "/w", speed=4)["PX4_SIM_SPEED_FACTOR"] == "4"


def test_the_commands():
    assert run.gz_command("/w/worlds/pcs14.sdf") == [
        "gz", "sim", "-s", "-r", "--verbose=2", "/w/worlds/pcs14.sdf"
    ]  # fmt: skip
    command = run.px4_command(TOOLS, "/work/run", instance=2)
    assert command[0] == "/home/me/px4/PX4-Autopilot/build/px4_sitl_default/bin/px4"
    assert command[1:] == [
        "-i", "2", "-d", "/home/me/px4/PX4-Autopilot/build/px4_sitl_default/etc", "-w", "/work/run"
    ]  # fmt: skip
    assert run.model_name(2, "pcs14_base") == "pcs14_base_2"


def test_the_plugins_printed_events_become_marks():
    text = "[Msg] Loaded system\n[pcs14-drag] chute fired at 63.204\nother stuff\n"
    assert run.gz_marks(text) == [(63.204, "chute fired")]
    assert run.gz_marks("nothing here") == []


def _free_port() -> int:
    with socket.socket(socket.AF_INET, socket.SOCK_DGRAM) as s:
        s.bind(("127.0.0.1", 0))
        return s.getsockname()[1]


def test_the_relay_passes_both_ways_until_the_uplink_is_cut():
    async def scenario():
        loop = asyncio.get_running_loop()
        px4_port, sdk_port = _free_port(), _free_port()
        heard = {"px4": [], "sdk": []}

        class Ear(asyncio.DatagramProtocol):
            def __init__(self, who):
                self.who = who

            def datagram_received(self, data, addr):
                heard[self.who].append((data, addr))

        px4, _ = await loop.create_datagram_endpoint(
            lambda: Ear("px4"), local_addr=("127.0.0.1", 0)
        )
        sdk, _ = await loop.create_datagram_endpoint(
            lambda: Ear("sdk"), local_addr=("127.0.0.1", sdk_port)
        )
        relay = await run.Relay(px4_port, sdk_port).start()

        async def settle():
            await asyncio.sleep(0.1)

        px4.sendto(b"telemetry", ("127.0.0.1", px4_port))
        await settle()
        assert [d for d, _ in heard["sdk"]] == [b"telemetry"]
        sdk.sendto(b"command", heard["sdk"][0][1])  # MAVSDK answers whoever spoke
        await settle()
        assert [d for d, _ in heard["px4"]] == [b"command"]
        assert heard["px4"][0][1][1] == px4_port  # PX4 hears its usual port answering

        relay.cut = True
        sdk.sendto(b"lost", heard["sdk"][0][1])
        px4.sendto(b"still telemetry", ("127.0.0.1", px4_port))
        await settle()
        assert [d for d, _ in heard["px4"]] == [b"command"]
        assert heard["sdk"][-1][0] == b"still telemetry"
        assert relay.dropped == 1

        relay.cut = False
        sdk.sendto(b"back", heard["sdk"][0][1])
        await settle()
        assert heard["px4"][-1][0] == b"back"
        relay.close()
        px4.close()
        sdk.close()

    asyncio.run(scenario())


async def _stamps(values, gap=0.0):
    for v in values:
        yield v
        await asyncio.sleep(gap)


def test_the_clock_keeps_px4s_time():
    async def scenario():
        clock = run.Clock()
        follow = asyncio.create_task(clock.follow(_stamps(range(0, 2_000_000, 10_000), 0.0005)))
        await clock.started()
        start = clock.now
        await clock.sleep(0.5)
        assert clock.now - start == pytest.approx(0.5, abs=0.02)
        flag = {"up": False}

        async def later():
            await clock.sleep(0.2)
            flag["up"] = True

        task = asyncio.create_task(later())
        assert await clock.until(lambda: flag["up"], timeout=1.0)
        assert not await clock.until(lambda: False, timeout=0.1)
        await task
        follow.cancel()

    asyncio.run(scenario())


def test_a_clock_that_stops_is_a_hung_sim():
    async def scenario():
        clock = run.Clock(stall_s=0.2)
        follow = asyncio.create_task(clock.follow(_stamps([1_000_000])))
        await clock.started()
        with pytest.raises(run.SimError, match="clock stopped"):
            await clock.sleep(1.0)
        follow.cancel()

    asyncio.run(scenario())
