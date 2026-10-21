"""Plain-English missions (#26): what I say becomes a plan, a deterministic checker validates the
plan against the active limits profile and the drone, I approve it, and the flight controller
flies it. The language model never commands the motors: it only writes a plan, as JSON in a
fixed shape, and a plan that doesn't parse or doesn't pass the checker never flies.

The checker mirrors my firmware's own limits (firmware/core's limits.hpp): the profile's
ceiling, the parachute rule without P, the top speed, and the energy, which is every leg flown at
its speed, home again, against what's left above the reserve. The geofence the firmware enforces
itself; the plan's distance from home is checked against the profile's fence where it has one.
"""

import json
import math
import re
from collections.abc import Callable
from dataclasses import dataclass, field

from pydantic import BaseModel, ValidationError

PARACHUTE_RULE_M = 30.0  # firmware/core's kParachuteRuleM
ENERGY_MARGIN = 1.25


class Waypoint(BaseModel):
    north_m: float
    east_m: float
    height_m: float
    speed_ms: float = 8.0
    hold_s: float = 0.0


class Plan(BaseModel):
    name: str
    waypoints: list[Waypoint]
    end: str = "return"  # "return" home or "land" at the last waypoint


@dataclass(frozen=True)
class Profile:
    name: str
    ceiling_m: float = 0.0  # 0 is none
    fence_m: float = 0.0


# firmware/core's limits.cpp, by name
PROFILES = {
    "max": Profile("max"),
    "us-recreational": Profile("us-recreational", ceiling_m=121.92),  # 400 ft
}


@dataclass(frozen=True)
class Drone:
    chute: bool  # P fitted
    battery_wh: float  # what's in the pack now
    reserve_wh: float
    power: Callable[[float], float]  # W at an airspeed, the sizing model's curve
    max_speed_ms: float


@dataclass(frozen=True)
class Checked:
    problems: list = field(default_factory=list)
    energy_wh: float = 0.0

    @property
    def ok(self) -> bool:
        return not self.problems


def check(plan: Plan, drone: Drone, profile: Profile) -> Checked:
    problems = []
    ceiling = profile.ceiling_m or math.inf
    if not drone.chute:
        ceiling = min(ceiling, PARACHUTE_RULE_M)
    here, energy = (0.0, 0.0), 0.0
    for k, w in enumerate(plan.waypoints, start=1):
        if w.height_m > ceiling:
            why = "the parachute rule (no P)" if not drone.chute and (
                not profile.ceiling_m or PARACHUTE_RULE_M < profile.ceiling_m) else (
                f"the {profile.name} ceiling")  # fmt: skip
            problems.append(f"waypoint {k} is {w.height_m:g} m up, over {why} at {ceiling:g} m")
        if w.speed_ms > drone.max_speed_ms:
            problems.append(f"waypoint {k} asks for {w.speed_ms:g} m/s, faster than the "
                            f"{drone.max_speed_ms:g} m/s the drone may fly")  # fmt: skip
        out = math.hypot(w.north_m, w.east_m)
        if profile.fence_m and out > profile.fence_m:
            problems.append(f"waypoint {k} is {out:.0f} m from home, past the fence")
        leg = math.hypot(w.north_m - here[0], w.east_m - here[1])
        speed = max(w.speed_ms, 0.5)
        energy += drone.power(speed) * (leg / speed + w.hold_s) / 3600.0
        here = (w.north_m, w.east_m)
    if plan.end == "return":
        cruise = min(8.0, drone.max_speed_ms)
        energy += drone.power(cruise) * (math.hypot(*here) / cruise) / 3600.0
    spare = drone.battery_wh - drone.reserve_wh
    if spare < ENERGY_MARGIN * energy:
        problems.append(f"not enough energy: it needs {energy:.0f} Wh with a "
                        f"{ENERGY_MARGIN:g}x margin, and there's {spare:.0f} Wh "
                        "above the reserve")  # fmt: skip
    return Checked(problems, energy)


class NoPlan(ValueError):
    """The model didn't write a plan in the shape asked for."""


PROMPT = """You turn a drone pilot's request into a flight plan. Reply with JSON only, no other
words, in exactly this shape:
{{"name": "<short name>", "end": "return" or "land",
  "waypoints": [{{"north_m": <m north of home>, "east_m": <m east of home>,
                  "height_m": <m above home>, "speed_ms": <m/s>, "hold_s": <s to wait there>}}]}}
Home is (0, 0). The pilot said: {words}"""


def plan_from_words(words: str, ask: Callable[[str], str]) -> Plan:
    """Asks the model (`ask(prompt)` gives its reply) for a plan, and reads it back through the
    plan's shape. Raises NoPlan if what comes back isn't one."""
    reply = ask(PROMPT.format(words=words))
    found = re.search(r"\{.*\}", reply, re.S)
    if found is None:
        raise NoPlan(f"no JSON in the reply: {reply[:120]!r}")
    try:
        return Plan.model_validate(json.loads(found.group(0)))
    except (json.JSONDecodeError, ValidationError) as error:
        raise NoPlan(str(error)) from error


def ollama(model: str = "qwen2.5:7b-instruct", host: str = "http://127.0.0.1:11434"):
    """`ask` through a local Ollama server: no key, no network beyond this machine."""
    import urllib.request

    def ask(prompt: str) -> str:
        body = json.dumps({"model": model, "prompt": prompt, "stream": False,
                           "options": {"temperature": 0}}).encode()  # fmt: skip
        request = urllib.request.Request(f"{host}/api/generate", data=body,
                                         headers={"Content-Type": "application/json"})  # fmt: skip
        with urllib.request.urlopen(request, timeout=120) as reply:
            return json.loads(reply.read())["response"]

    return ask
