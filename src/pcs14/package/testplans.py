"""The test plans: bench checks with the props off, then first flights, tethered first, each
check with what passes. Every safety rule gets a test, and every unproven item's first
measurement has its place in the plan.

The numbers come from the reports: the hover current each combination should draw (the
electrical report's pessimistic hover case), the supplies' voltages, the safety monitor's
timeout.
"""

from dataclasses import dataclass


@dataclass(frozen=True)
class Check:
    what: str
    passes: str  # what counts as a pass
    rule: str = ""  # the safety rule it tests, if it's one of them


BENCH = (
    (
        "First power",
        (
            Check(
                "The pack through a smoke stopper (a bulb or a fuse in series) on the XT60.",
                "The bulb glows and dims as the ESC's capacitors charge, then stays dim. A "
                "bulb that stays bright is a short: unplug at once and go back to the wiring "
                "guide's checks.",
            ),
            Check(
                "The supplies, with a meter: the BEC's 5 V at a module socket, the flight "
                "controller's 5 V, the 3.3 V regulators.",
                "5 V rails between 4.9 and 5.3 V; 3.3 V between 3.2 and 3.4 V.",
            ),
            Check(
                "The idle current, on the pack's lead.",
                "Under 1 A with the modules off; write it down, it's the avionics' real draw.",
            ),
        ),
    ),
    (
        "The radio and the kill switch",
        (
            Check(
                "Bind the receiver to the transmitter, and set the kill switch on its own "
                "two-position switch.",
                "The flight controller sees every stick and the switch.",
            ),
            Check(
                "The transmitter switched off with the drone armed, props off.",
                "The flight controller's RC failsafe fires (land, or as set) within a second.",
            ),
            Check(
                "Arm, raise the throttle a little, flip the kill switch.",
                "Every motor stops at once and stays stopped until the switch goes back and "
                "the drone is re-armed.",
                "My transmitter and kill switch override everything",
            ),
        ),
    ),
    (
        "The motors, props off",
        (
            Check(
                "PX4's motor test, one motor at a time.",
                "Each spins in its place (1 front right, 2 back left, 3 front left, 4 back "
                "right) and the right way; swap any two of a motor's three wires to reverse "
                "it.",
            ),
            Check(
                "Each prop on a prop balancer before it ever goes on.",
                "It sits level at any angle. The arms ring sideways close to what an "
                "unbalanced prop shakes them at in a hover (the structure report).",
            ),
            Check(
                "The current at a hover's throttle, all four, props off.",
                "A few amps at most: props off, there's no load. This is only a smoke check.",
            ),
        ),
    ),
    (
        "The sensors",
        (
            Check(
                "The accelerometer, gyro and compass calibrations in QGroundControl, and the "
                "attitude on its screen as the drone is tipped by hand.",
                "Tip the nose down and the display's nose goes down; the same for each axis.",
            ),
            Check(
                "The TF-Luna, held over the floor at known heights.",
                "Within 6 cm under 3 m, and 2% beyond, its datasheet's accuracy.",
            ),
            Check("The GPS outdoors with a clear sky.", "A 3D fix with ten or more satellites."),
            Check(
                "The Remote ID module, with a phone app that reads Remote ID (Drone Scanner, "
                "or the FAA's list of apps).",
                "The phone shows the module's serial number and the drone's position.",
            ),
        ),
    ),
    (
        "The safety monitor",
        (
            Check(
                "With the motors spinning slowly (props off), the kill switch through the "
                "safety monitor alone (the flight controller's own kill path disabled for the "
                "test).",
                "The motors stop: the switch reaches them through both boards.",
                "The kill switch reaches the motors through two separate boards",
            ),
            Check(
                "The Teensy unplugged while the motors spin slowly.",
                "The motors keep spinning: a dead safety monitor never stops the drone.",
                "If the safety monitor loses power, the drone keeps flying",
            ),
            Check(
                "A monitor cut, with a meter on the ESC's signal lines and on the main power.",
                "The signal lines go quiet; the main power never drops.",
                "The safety monitor cuts the ESC signal lines, never the main power",
            ),
            Check(
                "The monitor's automatic triggers, shaken and dropped by hand onto a cushion "
                "with the motors off.",
                "The log shows each trigger firing, and no cut: shadow mode.",
                "The automatic triggers stay in shadow mode until they've shown zero false "
                "triggers",
            ),
            Check(
                "The flight controller halted in a debugger with the motors spinning slowly.",
                "The motors stop within the monitor's 0.25 s timeout plus the ESC's own DShot "
                "timeout: never stuck at the last throttle.",
                "A hung CPU means the motors stop",
            ),
        ),
    ),
    (
        "The companion computer and the parachute",
        (
            Check(
                "V's Pi unplugged with the drone armed, props off.",
                "The flight controller's companion-lost failsafe fires, and it keeps flying "
                "its own modes.",
                "The flight controller never depends on the companion computer",
            ),
            Check(
                "With P fitted: the chute switch, props off, the canopy out of its tube and "
                "the release watched.",
                "The motors stop first, then the release servo moves; the log shows the order. "
                "Without P fitted the switch does nothing.",
                "The motors cut before the parachute deploys",
            ),
            Check(
                "A plan from plain English, never approved, sent to the drone.",
                "It doesn't fly. Only an approved plan the checker passed can.",
                "The LLM never commands the motors",
            ),
        ),
    ),
)

FLIGHTS = (
    Check(
        "PX4, tethered: a hover at 1 m for 30 s, the tether shorter than the props' reach "
        "of anything, in a field with nobody inside 30 m.",
        "It holds level and its height; the current stays under the hover current "
        "below; a gyro log for the vibration.",
    ),
    Check(
        "PX4, tethered: small stick steps in roll and pitch, then three stick doublets "
        "(a quarter stick each way, a quarter second).",
        "It settles without oscillating. The doublets' log goes to self-tuning's fit.",
    ),
    Check(
        "PX4, free: hover at 3 m, then 10 m, in position mode.",
        "It holds within a meter; the pack's voltage sags no more than the sizing model says.",
    ),
    Check(
        "PX4: the failsafes, one at a time, high enough to recover: the transmitter off "
        "(return), the pack's low-battery warning (on a part-used pack).",
        "Each does what it's set to.",
    ),
    Check(
        "My firmware, after its register-level drivers pass on the bench against PX4 on "
        "the same board: the same tethered hover, then everything above again.",
        "The same passes as PX4's.",
    ),
)


def hover_currents(electrical: dict) -> dict[str, float]:
    """Each combination's pessimistic hover current, from the electrical report."""
    return {c["setup"]: c["battery_amps"] for c in electrical.get("cases", [])
            if c.get("case") == "hover"}  # fmt: skip


def safety_rules() -> list[str]:
    return [c.rule for _, checks in BENCH for c in checks if c.rule]


def render(electrical: dict, unproven_groups, generated: str) -> str:
    """`unproven_groups`: (name, [Unproven]) from decisions.md and each report."""
    out = [
        "# The test plans",
        "",
        f"*Generated {generated} by `pcs14 package`. Bench checks first, props off, in this "
        "order; then the first flights, tethered first. Each check says what passes. A "
        "check that fails stops everything after it.*",
        "",
        "## On the bench, props off",
    ]
    for title, checks in BENCH:
        out += ["", f"### {title}", "", "| Check | Passes when | Safety rule |", "|---|---|---|"]
        out += [f"| {c.what} | {c.passes} | {c.rule} |" for c in checks]
    out += ["", "## The first flights", "",
            "PX4 first, then my firmware; tethered first, then free; in the `us-recreational` "
            "profile, with the props checked before every flight.", "",
            "| Flight | Passes when |", "|---|---|"]  # fmt: skip
    out += [f"| {c.what} | {c.passes} |" for c in FLIGHTS]
    hover = hover_currents(electrical)
    if hover:
        out += ["", "The hover current each combination should draw at most, from the "
                "electrical report's pessimistic hover at the reserve (a full pack draws less):",
                "", "| Combination | Hover |", "|---|---|"]  # fmt: skip
        out += [f"| {s} | {a:.1f} A |" for s, a in hover.items()]
    out += ["", "## The unproven list's measurements", "",
            "What the sims can't prove, and the first thing to measure for each, from "
            "decisions.md and every report. Most fit into the checks above; the rest need a "
            "thrust stand or a day of their own.", ""]  # fmt: skip
    for name, items in unproven_groups:
        rows = [u for u in items if u.measure]
        if not rows:
            continue
        out += [f"### {name}", "", "| What the sim can't prove | First to measure |", "|---|---|"]
        out += [f"| {u.what} | {u.measure} |" for u in rows]
        out += [""]
    return "\n".join(out)
