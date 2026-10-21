"""The legal checklist for flying it in the US, each rule with its source and the setting it
maps to. The rules stay settings, not caps (decisions.md): the limits profile carries the
legal numbers, and the hardware is built for what it can physically do.

The links are the FAA's and the FCC's own pages. They weren't opened on the day this was
written, so the checklist says so: check each one before relying on it, since rules change.
"""

from dataclasses import dataclass


@dataclass(frozen=True)
class Rule:
    what: str
    means: str  # what it means for this drone
    setting: str  # where it lives in the design, or "mine" for what only I can do
    source: str  # the agency's own page


RULES = (
    Rule(
        "Registration",
        "Recreational drones over 250 g have to be registered with the FAA, and the "
        "registration number marked on the outside. This one is over 2 kg in every "
        "combination.",
        "mine: register in FAADroneZone before the first outdoor flight",
        "https://www.faa.gov/uas/recreational_flyers",
    ),
    Rule(
        "The TRUST certificate",
        "Recreational flyers pass The Recreational UAS Safety Test, free and online, and "
        "carry proof of it.",
        "mine",
        "https://www.faa.gov/uas/recreational_flyers",
    ),
    Rule(
        "Remote ID",
        "The drone broadcasts its identity and position. A broadcast module does it for "
        "drones without it built in: the Ruko R111 on Base's mount, its serial number "
        "added to the registration.",
        "the Remote ID module (Base); the firmware doesn't refuse to arm without it",
        "https://www.faa.gov/uas/getting_started/remote_id",
    ),
    Rule(
        "The 400 ft ceiling",
        "Recreational flights stay at or under 400 ft above the ground in uncontrolled airspace.",
        "the us-recreational limits profile's ceiling, 121.92 m",
        "https://www.faa.gov/uas/recreational_flyers",
    ),
    Rule(
        "Controlled airspace",
        "Flying in controlled airspace near airports needs an authorization first (LAANC, "
        "through an approved app); B4UFLY shows where that applies.",
        "mine: checked before every flight; the geofence can be set to keep out",
        "https://www.faa.gov/uas/getting_started/b4ufly",
    ),
    Rule(
        "Line of sight",
        "Recreational flights stay within the pilot's visual line of sight. HaLow reaches "
        "several kilometers; that's the hardware, not permission to use it.",
        "mine; the us-recreational profile's geofence radius can be set to match",
        "https://www.faa.gov/uas/recreational_flyers",
    ),
    Rule(
        "Part 107",
        "Anything beyond recreational (paid work, or flights the recreational rules don't "
        "cover, through waivers) needs the Part 107 certificate.",
        "mine: whether to get it is still open",
        "https://www.faa.gov/uas/commercial_operators",
    ),
    Rule(
        "The radios",
        "ExpressLRS on 2.4 GHz, HaLow and the Meshtastic relay on 902 to 928 MHz are "
        "unlicensed devices under FCC Part 15, used at their certified settings.",
        "each radio's power setting, per radio; the us-recreational profile expects the "
        "US settings",
        "https://www.ecfr.gov/current/title-47/chapter-I/subchapter-A/part-15",
    ),
)


def render(generated: str) -> str:
    out = [
        "# The legal checklist (US)",
        "",
        f"*Generated {generated} by `pcs14 package`. Each rule, what it means for this drone, "
        "and where it lives: the limits profile, a part, or me. The rules are settings, not "
        "caps (decisions.md): the `us-recreational` profile carries the legal numbers and the "
        "`max` profile only the physical ones. The links are the FAA's and the FCC's own "
        "pages, not opened on the day this was written, and rules change: check each before "
        "relying on it. This isn't legal advice.*",
        "",
        "| Rule | What it means here | Where it lives | Source |",
        "|---|---|---|---|",
    ]
    out += [f"| {r.what} | {r.means} | {r.setting} | [{r.source}]({r.source}) |" for r in RULES]
    out += [
        "",
        "Before the first outdoor flight: registered, the number on the drone, TRUST passed, "
        "the Remote ID module fitted and checked with a phone, the `us-recreational` profile "
        "loaded (the ground station shows which one is on), and the airspace checked.",
        "",
    ]
    return "\n".join(out)
