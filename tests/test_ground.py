"""The ground station's page and server, with a fake drone behind them."""

import asyncio
import json
import urllib.request

from pcs14.ground import web
from pcs14.ground.station import PROFILES, TUNING


class FakeStation:
    def __init__(self):
        self.state = {"connected": True, "mode": "HOLD", "height_m": 12.5, "limits": "max",
                      "params": {"MC_ROLL_P": 9.0, "PCS14_LIMITS": 0}}  # fmt: skip
        self.asked = []

    def snapshot(self):
        return dict(self.state)

    async def set_param(self, name, value):
        self.asked.append((name, value))
        self.state["params"][name] = value
        return value


def serve(station):
    server = web.serve(station, port=0, run_coroutine=asyncio.run)
    return server, f"http://127.0.0.1:{server.server_address[1]}"


def test_the_page_carries_the_limits_profile_and_the_tuning():
    server, url = serve(FakeStation())
    try:
        page = urllib.request.urlopen(url + "/").read().decode()
    finally:
        server.shutdown()
    assert 'id="limits"' in page and "us-recreational" in page
    for name in TUNING:
        assert name in page


def test_the_state_and_the_live_feed():
    server, url = serve(FakeStation())
    try:
        state = json.loads(urllib.request.urlopen(url + "/state").read())
        feed = urllib.request.urlopen(url + "/events?n=2").read().decode()
    finally:
        server.shutdown()
    assert state["mode"] == "HOLD" and state["limits"] == "max"
    events = [json.loads(line[6:]) for line in feed.splitlines() if line.startswith("data: ")]
    assert len(events) == 2 and events[0]["height_m"] == 12.5


def test_a_parameter_set_goes_to_the_drone_and_comes_back():
    station = FakeStation()
    server, url = serve(station)
    try:
        body = json.dumps({"name": "MC_ROLL_P", "value": 8.0}).encode()
        reply = json.loads(urllib.request.urlopen(url + "/param", data=body).read())
    finally:
        server.shutdown()
    assert reply == {"name": "MC_ROLL_P", "value": 8.0}
    assert station.asked == [("MC_ROLL_P", 8.0)]


def test_the_profiles_are_the_firmwares():
    assert PROFILES == {0: "max", 1: "us-recreational"}


def test_the_drones_messages_are_kept_newest_last():
    """Status texts (a preflight failure, "safety monitor quiet") show on the page."""
    from types import SimpleNamespace as NS

    from pcs14.ground.station import MESSAGES_KEPT, Station

    async def texts():
        for k in range(MESSAGES_KEPT + 2):
            yield NS(type="WARNING", text=f"message {k}")

    station = Station()
    station.drone = NS(telemetry=NS(status_text=texts))
    asyncio.run(station._status_text())
    got = station.snapshot()["messages"]
    assert len(got) == MESSAGES_KEPT
    assert got[-1] == {"type": "WARNING", "text": f"message {MESSAGES_KEPT + 1}",
                       "at": got[-1]["at"]}  # fmt: skip


def test_the_page_has_somewhere_to_show_them():
    server, url = serve(FakeStation())
    try:
        page = urllib.request.urlopen(url + "/").read().decode()
    finally:
        server.shutdown()
    assert 'id="messages"' in page


def test_the_battery_shows_its_current_and_charge_used():
    from types import SimpleNamespace as NS

    from pcs14.ground.station import Station

    async def readings():
        yield NS(voltage_v=24.1, remaining_percent=62.0, current_battery_a=18.5,
                 capacity_consumed_ah=3.4204)  # fmt: skip

    station = Station()
    station.drone = NS(telemetry=NS(battery=readings))
    asyncio.run(station._battery())
    s = station.snapshot()
    assert s["battery_a"] == 18.5 and round(s["battery_mah"]) == 3420
    server, url = serve(FakeStation())
    try:
        page = urllib.request.urlopen(url + "/").read().decode()
    finally:
        server.shutdown()
    assert 'id="current"' in page
