"""The Meshtastic relay (#30) as a link: a LoRa mesh node riding on the drone works like a
temporary cell tower, because radios like this need line of sight, and a node in the air sees
over what blocks two on the ground.

Each preset's link budget is Meshtastic's own (meshtastic.org/docs/overview/radio-settings, for
22 dBm into a 0 dBi antenna). The path is the same as HaLow's (pcs14.modules.halow): free space
to the breakpoint, then the ground's reflection, over flat ground at 915 MHz, with a 10 dB fade
margin. And the radio horizon caps it, since the Earth curves away: 4.12 (sqrt h1 + sqrt h2) km,
the usual figure with the atmosphere bending the signal a little over the edge.
"""

import math

from pcs14.modules.halow import breakpoint_m, wavelength_m

# dB, 22 dBm into 0 dBi (Meshtastic's table)
PRESETS = {
    "ShortTurbo": 140.0, "ShortFast": 143.0, "ShortSlow": 145.5, "MediumTurbo": 145.0,
    "MediumFast": 148.0, "MediumSlow": 150.5, "LongTurbo": 150.0, "LongFast": 153.0,
    "LongModerate": 156.0,
}  # fmt: skip
MARGIN_DB = 10.0


def horizon_m(height_a_m: float, height_b_m: float) -> float:
    return 4120.0 * (math.sqrt(height_a_m) + math.sqrt(height_b_m))


def reach_m(preset: str, height_a_m: float, height_b_m: float,
            margin_db: float = MARGIN_DB) -> float:  # fmt: skip
    """How far two nodes at these heights hold the preset, over flat ground."""
    allowed = PRESETS[preset] - margin_db
    free = wavelength_m() * 10 ** (allowed / 20) / (4 * math.pi)
    if free <= breakpoint_m(height_a_m, height_b_m):
        reach = free
    else:
        reach = 10 ** ((allowed + 20 * math.log10(height_a_m * height_b_m)) / 40)
    return min(reach, horizon_m(height_a_m, height_b_m))
