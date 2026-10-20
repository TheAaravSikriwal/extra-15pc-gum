"""The ground station's link to the drone: MAVSDK, keeping the latest of everything.

It listens where PX4 and my firmware send a ground station's MAVLink (UDP 14550, plus the
instance in the sim), follows the telemetry into one snapshot, and reads and writes the
parameters that tune the drone in flight and pick its limits profile. The web page
(pcs14.ground.web) shows the snapshot and sends the changes."""

import asyncio
import contextlib
import time

# what the page can tune, by parameter, with what each one is (shown next to it)
TUNING = {
    "PCS14_ANGLE_P": "self-level: roll and pitch angle gain (1/s)",
    "PCS14_YAW_P": "self-level: heading gain (1/s)",
    "PCS14_RATE_P": "rate loops, roll and pitch: P (rad/s^2 per rad/s)",
    "PCS14_RATE_I": "rate loops, roll and pitch: I",
    "PCS14_RATE_D": "rate loops, roll and pitch: D",
    "PCS14_YAWRATE_P": "rate loop, yaw: P",
}
INTS = {"PCS14_LIMITS"}  # int32 parameters; the rest are floats
PROFILES = {0: "max", 1: "us-recreational"}  # PCS14_LIMITS, as firmware/core's limits.hpp has
MESSAGES_KEPT = 8  # the drone's latest status texts, shown on the page


class Station:
    """One drone. `start` connects and follows; `snapshot` is the latest of everything;
    `set_param` changes one parameter and returns what the drone echoed back."""

    def __init__(self, address: str = "udpin://0.0.0.0:14550", grpc_port: int = 50060):
        self.address, self.grpc_port = address, grpc_port
        self.drone = None
        self.loop: asyncio.AbstractEventLoop | None = None
        self.state: dict = {"connected": False, "params": {}, "messages": [], "updated": 0.0}
        self._tasks: list = []

    async def start(self, timeout_s: float = 60.0):
        from mavsdk import System

        self.loop = asyncio.get_running_loop()
        self.drone = System(port=self.grpc_port)
        await self.drone.connect(system_address=self.address)

        async def connected():
            async for status in self.drone.core.connection_state():
                if status.is_connected:
                    return

        await asyncio.wait_for(connected(), timeout_s)
        self.state["connected"] = True
        for follow in (self._attitude, self._position, self._battery, self._mode,
                       self._armed, self._landed, self._status_text):  # fmt: skip
            self._tasks.append(asyncio.create_task(follow()))
        await self.refresh_params()

    async def stop(self):
        for task in self._tasks:
            task.cancel()
        for task in self._tasks:
            with contextlib.suppress(BaseException):
                await task
        stop = getattr(self.drone, "_stop_mavsdk_server", None)
        if stop is not None:
            with contextlib.suppress(Exception):
                stop()

    def _set(self, **values):
        self.state.update(values)
        self.state["updated"] = time.time()

    async def _attitude(self):
        async for a in self.drone.telemetry.attitude_euler():
            self._set(roll_deg=a.roll_deg, pitch_deg=a.pitch_deg, yaw_deg=a.yaw_deg)

    async def _position(self):
        async for p in self.drone.telemetry.position_velocity_ned():
            v = p.velocity
            self._set(north_m=p.position.north_m, east_m=p.position.east_m,
                      height_m=-p.position.down_m,
                      speed_m_s=(v.north_m_s**2 + v.east_m_s**2) ** 0.5,
                      climb_m_s=-v.down_m_s)  # fmt: skip

    async def _battery(self):
        async for b in self.drone.telemetry.battery():
            used = getattr(b, "capacity_consumed_ah", None)  # the fuel gauge's count
            mah = None if used is None or used != used else used * 1000  # NaN when there's none
            self._set(battery_v=b.voltage_v, battery_pct=b.remaining_percent,
                      battery_a=getattr(b, "current_battery_a", None), battery_mah=mah)  # fmt: skip

    async def _mode(self):
        async for m in self.drone.telemetry.flight_mode():
            self._set(mode=str(m))

    async def _armed(self):
        async for a in self.drone.telemetry.armed():
            self._set(armed=a)

    async def _landed(self):
        async for in_air in self.drone.telemetry.in_air():
            self._set(in_air=in_air)

    async def _status_text(self):
        """What the drone says: why it won't arm, a failsafe, the safety monitor gone quiet."""
        async for m in self.drone.telemetry.status_text():
            kept = self.state["messages"][-(MESSAGES_KEPT - 1) :]
            kept.append({"type": str(m.type), "text": m.text, "at": time.time()})
            self._set(messages=kept)

    async def refresh_params(self):
        """Reads the tuning and the limits profile off the drone."""
        params = {}
        for name in [*TUNING, *INTS]:
            try:
                if name in INTS:
                    params[name] = await self.drone.param.get_param_int(name)
                else:
                    params[name] = await self.drone.param.get_param_float(name)
            except Exception:  # noqa: BLE001 (a drone without it: PX4 has no PCS14_ ones)
                continue
        self.state["params"] = params
        self._set(limits=PROFILES.get(params.get("PCS14_LIMITS", 0), "max"))

    async def set_param(self, name: str, value: float):
        """Sets one parameter; returns the value the drone has afterwards."""
        if name in INTS:
            await self.drone.param.set_param_int(name, int(value))
        else:
            await self.drone.param.set_param_float(name, float(value))
        await self.refresh_params()
        return self.state["params"].get(name)

    def snapshot(self) -> dict:
        return {k: v for k, v in self.state.items()}
