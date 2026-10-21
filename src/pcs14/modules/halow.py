"""Wi-Fi HaLow (802.11ah) as a link, for module V's data and video: what rate it holds at each
distance, and where it starts dropping packets.

The radio's numbers are Morse Micro's, for the MM6108 chip that Heltec's card is built on: the
receive sensitivity at each rate on a 2 MHz channel (10% packet error, 1000-byte packets) and
the transmit power, 21 dBm at the lowest rate easing to 17 dBm at MCS7, both from Morse Micro's
MM6108-MF08651-US module datasheet (v102, Table 9 and Table 10,
https://www.morsemicro.com/resources/datasheets/modules/MM6108-MF08651-US_Data_Sheet.pdf).
Heltec publishes no sensitivity for its own card, so these are estimates for it: same chip,
its own front end.

The path is line of sight over flat ground at 915 MHz: free space out to the breakpoint, where
the ground's reflection starts cancelling the direct ray, and the two-ray model's 40 dB a
decade past it. The fade margin (10 dB) stands for everything that model leaves out: the
drone's own body in the way as it turns, multipath, and a laptop that isn't held up high.
Trees and hills aren't in it at all.
"""

import math
from dataclasses import dataclass

C = 299_792_458.0  # m/s
FREQUENCY_HZ = 915e6  # the middle of the US band, 902 to 928 MHz


@dataclass(frozen=True)
class Rate:
    mcs: int
    mbps: float  # the PHY rate, short guard interval
    sensitivity_dbm: float


# a 2 MHz channel, one spatial stream (Morse Micro's Table 9)
RATES_2MHZ = (
    Rate(0, 0.72, -103), Rate(1, 1.4, -100), Rate(2, 2.2, -97), Rate(3, 2.9, -94),
    Rate(4, 4.3, -90), Rate(5, 5.8, -87), Rate(6, 6.5, -85), Rate(7, 7.2, -84),
)  # fmt: skip


def wavelength_m(frequency_hz: float = FREQUENCY_HZ) -> float:
    return C / frequency_hz


def free_space_loss_db(distance_m: float, frequency_hz: float = FREQUENCY_HZ) -> float:
    return 20 * math.log10(4 * math.pi * distance_m / wavelength_m(frequency_hz))


def breakpoint_m(height_a_m: float, height_b_m: float, frequency_hz: float = FREQUENCY_HZ):
    """Where the ground's reflection starts to cancel the direct ray."""
    return 4 * math.pi * height_a_m * height_b_m / wavelength_m(frequency_hz)


def path_loss_db(distance_m: float, height_a_m: float, height_b_m: float,
                 frequency_hz: float = FREQUENCY_HZ) -> float:  # fmt: skip
    """Free space to the breakpoint, then the two-ray model's 40 log10(d) - 20 log10(h1 h2)."""
    if distance_m <= breakpoint_m(height_a_m, height_b_m, frequency_hz):
        return free_space_loss_db(distance_m, frequency_hz)
    return 40 * math.log10(distance_m) - 20 * math.log10(height_a_m * height_b_m)


@dataclass(frozen=True)
class Link:
    tx_mcs0_dbm: float = 21.0  # Morse Micro's typical at 3.3 V, easing to MCS7's
    tx_mcs7_dbm: float = 17.0
    antenna_dbi: float = 2.0  # each end: a plain dipole
    losses_db: float = 2.0  # cables and connectors, both ends together
    margin_db: float = 10.0  # the fade margin
    ground_height_m: float = 1.5  # the laptop's antenna
    rates: tuple = RATES_2MHZ

    def tx_dbm(self, mcs: int) -> float:
        share = min(max(mcs, 0), 7) / 7
        return self.tx_mcs0_dbm + (self.tx_mcs7_dbm - self.tx_mcs0_dbm) * share

    def _rate(self, mcs: int) -> Rate:
        return next(r for r in self.rates if r.mcs == mcs)

    def received_dbm(self, distance_m: float, height_m: float, mcs: int = 0) -> float:
        budget = self.tx_dbm(mcs) + 2 * self.antenna_dbi - self.losses_db
        return budget - path_loss_db(max(distance_m, 1.0), height_m, self.ground_height_m)

    def reach_m(self, mcs: int, height_m: float, margin_db: float | None = None) -> float:
        """How far `mcs` holds with its margin, at the drone's height."""
        margin = self.margin_db if margin_db is None else margin_db
        allowed = (self.tx_dbm(mcs) + 2 * self.antenna_dbi - self.losses_db
                   - self._rate(mcs).sensitivity_dbm - margin)  # fmt: skip
        free = wavelength_m() * 10 ** (allowed / 20) / (4 * math.pi)
        if free <= breakpoint_m(height_m, self.ground_height_m):
            return free
        return 10 ** ((allowed + 20 * math.log10(height_m * self.ground_height_m)) / 40)

    def rate_mbps(self, distance_m: float, height_m: float) -> float:
        """The fastest rate with its margin at this distance, or 0 past the slowest one's."""
        held = [r.mbps for r in self.rates if distance_m <= self.reach_m(r.mcs, height_m)]
        return max(held, default=0.0)

    def packet_loss(self, distance_m: float, height_m: float) -> float:
        """The share of packets lost on the slowest rate, which the link falls back to at its
        edge: the rated 10% at the sensitivity, ten times less for every 2 dB above it."""
        slowest = min(self.rates, key=lambda r: r.mcs)
        above = self.received_dbm(distance_m, height_m, slowest.mcs) - slowest.sensitivity_dbm
        return min(1.0, 0.1 * 10 ** (-above / 2))
