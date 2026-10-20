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
