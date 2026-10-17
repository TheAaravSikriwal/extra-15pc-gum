"""The battery: each cell's resting-voltage curve plus its internal resistance, scaled to the
pack, plus the wiring between the pack and the ESC.

Under load the pack sags: terminal voltage = resting voltage - current x resistance. When the
drone asks for a power rather than a current, the current comes from solving
    R I^2 - V_rest I + P = 0
which is where sag and current feed each other: more sag means more current for the same
power, which means more sag. If that has no answer, the pack can't deliver the power at all.
"""

import bisect
import math
from dataclasses import dataclass

from pcs14 import units
from pcs14.design import PackSpec


@dataclass(frozen=True)
class Pack:
    spec: PackSpec

    def __post_init__(self):
        curve = self.spec.cell.ocv_curve
        object.__setattr__(self, "_socs", [p.soc for p in curve])
        object.__setattr__(self, "_volts", [p.voltage_v for p in curve])

    @property
    def capacity(self) -> float:
        """Coulombs."""
        return self.spec.parallel * self.spec.cell.capacity

    @property
    def capacity_mah(self) -> float:
        return units.coulomb_to_mah(self.capacity)

    @property
    def resistance(self) -> float:
        cell = self.spec.cell
        return self.spec.series * cell.internal_resistance / self.spec.parallel + (
            self.spec.wiring_resistance
        )

    @property
    def max_continuous_current(self) -> float:
        return self.spec.parallel * self.spec.cell.max_continuous_a

    @property
    def min_voltage(self) -> float:
        return self.spec.series * self.spec.cell.min_voltage_v

    def ocv(self, soc: float) -> float:
        """Resting (open-circuit) voltage at a state of charge between 0 and 1."""
        socs, volts = self._socs, self._volts
        if soc <= socs[0]:
            return self.spec.series * volts[0]
        if soc >= socs[-1]:
            return self.spec.series * volts[-1]
        i = bisect.bisect_right(socs, soc)
        fraction = (soc - socs[i - 1]) / (socs[i] - socs[i - 1])
        return self.spec.series * (volts[i - 1] + fraction * (volts[i] - volts[i - 1]))

    def terminal_voltage(self, soc: float, current: float) -> float:
        return self.ocv(soc) - current * self.resistance

    def current_for_power(self, soc: float, power: float) -> float | None:
        """The current that delivers `power` watts after sag, or None if the pack can't."""
        rest, r = self.ocv(soc), self.resistance
        if power <= 0:
            return 0.0
        discriminant = rest * rest - 4 * r * power
        if discriminant < 0:
            return None
        return (rest - math.sqrt(discriminant)) / (2 * r)

    def drain(self, soc: float, current: float, seconds: float) -> float:
        """The state of charge after drawing `current` amps for `seconds`."""
        return soc - current * seconds / self.capacity

    def mah_used(self, soc: float) -> float:
        return (1 - soc) * self.capacity_mah

    def soc_at_reserve(self, reserve_fraction: float) -> float:
        """The reserve is counted in charge (mAh), so it sits at that state of charge."""
        return reserve_fraction
