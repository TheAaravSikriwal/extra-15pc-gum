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


def test_a_one_shot_wait_closes_its_stream():
    closed = {"yes": False}

    async def stream():
        try:
            for k in range(100):
                yield k
                await asyncio.sleep(0)
        finally:
            closed["yes"] = True

    assert asyncio.run(run.first(stream(), lambda k: k == 3)) == 3
    assert closed["yes"]  # MAVSDK stops queueing for a stream once it's closed


def test_gazebo_message_types_map_to_their_python_modules():
    assert run.gz_message("gz.msgs.Vector3d") == ("gz.msgs10.vector3d_pb2", "Vector3d")
    assert run.gz_message("gz.msgs.Pose_V") == ("gz.msgs10.pose_v_pb2", "Pose_V")
    assert run.gz_message("gz.msgs.EntityFactory") == ("gz.msgs10.entity_factory_pb2",
                                                        "EntityFactory")  # fmt: skip


def test_topics_publish_in_our_partition_and_reuse_each_publisher():
    sent = []

    class Publisher:
        def has_connections(self):
            return True

        def publish(self, message):
            sent.append(message)

    class FakeNode:
        def __init__(self, options):
            self.options, self.advertised = options, []

        def advertise(self, topic, kind):
            self.advertised.append((topic, kind.__name__))
            return Publisher()

    class Options:
        partition = ""

    class Transport:
        NodeOptions, Node = Options, FakeNode

    class Vector3d:
        text = ""

    class Messages:
        pass

    Messages.Vector3d = Vector3d

    def parse(text, message):
        message.text = text

    topics = run.GzTopics(Transport, "pcs14_1_0", parse=parse, load=lambda module: Messages)
    for speed in (2, 4):
        asyncio.run(topics.publish("/pcs14/wind", "gz.msgs.Vector3d", f"x: {speed}"))
    assert topics.node.options.partition == "pcs14_1_0"
    assert topics.node.advertised == [("/pcs14/wind", "Vector3d")]
    assert [m.text for m in sent] == ["x: 2", "x: 4"]


def test_my_firmware_gets_its_parameters_with_their_types():
    text = run.params_text({"MC_ROLL_P": 9.0, "CA_ROTOR_COUNT": 4, "SDLOG_MODE": 2})
    assert text.splitlines() == ["CA_ROTOR_COUNT 4", "MC_ROLL_P 9.0", "SDLOG_MODE 2"]


def test_my_firmware_runs_on_px4s_ports_for_its_instance():
    command = run.sitl_command("/b/pcs14_sitl", "pcs14_base_3", "/m/firmware.txt", 3, "/r/p.txt")
    assert command[0] == "/b/pcs14_sitl"
    assert command[command.index("--instance") + 1] == "3"
    assert command[command.index("--model") + 1] == "pcs14_base_3"
    assert "--stdin" not in command


def test_the_safety_monitor_can_fire_the_chute_only_where_there_is_one():
    plain = run.monitor_command("/b/pcs14_monitor_sitl", "pcs14_base_0")
    assert "--chute" not in plain
    fitted = run.monitor_command("/b/pcs14_monitor_sitl", "pcs14_p_0", chute=True)
    assert fitted[-1] == "--chute"
    assert any(line.startswith(run.MONITOR_LINES) for line in ["chute released at 41.200"])


def test_my_firmwares_runs_keep_the_parachute_rule_off_unless_a_scenario_wants_it():
    assert run.mine_params({"MC_ROLL_P": 9.0})["PCS14_CHUTE_RULE"] == 0
    # the chute rule scenario is the one that switches it back on
    assert run.mine_params({"PCS14_CHUTE_RULE": 1})["PCS14_CHUTE_RULE"] == 1


def test_only_known_firmware_flies():
    with pytest.raises(ValueError, match="no firmware called betaflight"):
        run.Session(run.toolchain(), "pcs14_base", {}, "out", "smoke", firmware="betaflight")


def test_topics_answer_service_requests_and_keep_the_latest_poses():
    from types import SimpleNamespace as NS

    class FakeNode:
        def __init__(self, options):
            self.requests, self.subscribed = [], {}

        def request(self, service, request, request_type, reply_type, timeout):
            self.requests.append((service, request.text, request_type.__name__, timeout))
            return True, reply_type()

        def subscribe(self, kind, topic, callback):
            self.subscribed[topic] = (kind.__name__, callback)
            return True

    class Options:
        partition = ""

    class Transport:
        NodeOptions, Node = Options, FakeNode

    class Pose:
        text = ""

    class Boolean:
        text = "data: true"

    class Pose_V:  # noqa: N801 (Gazebo's name)
        pass

    messages = NS(Pose=Pose, Boolean=Boolean, Pose_V=Pose_V)

    def parse(text, message):
        message.text = text

    topics = run.GzTopics(Transport, "p", parse=parse, load=lambda module: messages,
                          show=lambda message: message.text)  # fmt: skip
    reply = topics.request("/world/w/set_pose", "gz.msgs.Pose", "gz.msgs.Boolean", 'name: "box"')
    assert reply == "data: true"
    assert topics.node.requests == [("/world/w/set_pose", 'name: "box"', "Pose", 5000)]
    assert topics.pose("drone") is None  # nothing heard yet
    topics.watch_poses("w")
    kind, callback = topics.node.subscribed["/world/w/pose/info"]
    pose = NS(name="drone", position=NS(x=1.0, y=4.0, z=1.5),
              orientation=NS(w=1.0, x=0.0, y=0.0, z=0.0))  # fmt: skip
    callback(NS(pose=[NS(name="other", position=pose.position, orientation=pose.orientation),
                      pose]))  # fmt: skip
    assert kind == "Pose_V"
    assert topics.pose("drone") == ((1.0, 4.0, 1.5), (1.0, 0.0, 0.0, 0.0))
