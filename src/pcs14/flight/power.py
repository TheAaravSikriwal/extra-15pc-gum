"""Power afterwards: Gazebo doesn't simulate electricity, so a flight's logged rotor speeds turn
into current here, through the same battery model the sizing model uses. Every layer then agrees
on what a battery is, and the reserve is counted in mAh everywhere.

A motor's electrical power comes from its thrust table, read by the thrust the sim's rotor made
(its motor constant times its logged speed squared). The sim's motor is a one-number fit that
isn't quite the table at the same speed (3% slow at the base combination's hover, which is 9%
in power), so reading by speed would put the fit's error into the energy; reading by thrust
keeps it out. For a given thrust the prop does the same work whatever the pack's voltage, so
only the current changes with it. `motor_power` reads by speed instead, for logs without a
motor model. The pack's current for that power, sag included, comes from the battery
model, and the charge drains sample by sample.
"""

import bisect
from dataclasses import dataclass


def motor_power(table, rpm: float) -> float:
    """W into one motor and its ESC, at `rpm`."""
    rows = [r for r in table.rows if r.rpm]
    rpms = [r.rpm for r in rows]
    if rpm <= rpms[0]:
        return rows[0].power * (rpm / rpms[0]) ** 3
    if rpm >= rpms[-1]:
        return rows[-1].power * (rpm / rpms[-1]) ** 3
    k = bisect.bisect_right(rpms, rpm)
    low, high = rows[k - 1], rows[k]
    share = (rpm - low.rpm) / (high.rpm - low.rpm)
    return low.power + share * (high.power - low.power)


def electrical_power(table, rpms, avionics_w: float) -> float:
    """W from the pack: every motor at its logged rpm, plus the avionics."""
    return sum(motor_power(table, r) for r in rpms) + avionics_w


def thrust_power(rotor, thrust: float) -> float:
    """W into one motor making `thrust` N, read off the (pessimistic) table by thrust. Past the
    table's top, power grows as thrust to the 1.5, the way a prop's does."""
    found = rotor.power_for_thrust(thrust)
    if found is not None:
        return found
    return rotor.max_power * (thrust / rotor.max_thrust) ** 1.5


def electrical_power_from_thrust(rotor, thrusts, avionics_w: float) -> float:
    """W from the pack, from the thrust each motor made in the sim (its motor constant times
    its speed squared). The sim's motor is a one-number fit that isn't quite the table at the
    same speed, and reading the power by thrust keeps that fit's error out of the energy."""
    return sum(thrust_power(rotor, t) for t in thrusts) + avionics_w


@dataclass(frozen=True)
class Drain:
    times: list  # s
    power: list  # W from the pack
    current: list  # A
    voltage: list  # V at the pack
    soc: list  # state of charge, 1 is full
    mah_used: list


def drain(pack, times, powers, start_soc: float = 1.0) -> Drain:
    """The pack through a logged flight: each sample's power held until the next one."""
    soc = start_soc
    out = Drain([], [], [], [], [], [])
    for k, (t, p) in enumerate(zip(times, powers, strict=True)):
        current = pack.current_for_power(soc, p)
        if current is None:
            raise ValueError(f"the pack can't give {p:.0f} W at {t:.1f} s")
        out.times.append(t)
        out.power.append(p)
        out.current.append(current)
        out.voltage.append(pack.terminal_voltage(soc, current))
        out.soc.append(soc)
        out.mah_used.append(pack.mah_used(soc))
        if k + 1 < len(times):
            soc = pack.drain(soc, current, times[k + 1] - t)
    return out


def endurance(pack, power_w: float, reserve_fraction: float, dt: float = 5.0) -> float:
    """Seconds at a steady `power_w` from a full pack down to the reserve, stepped exactly as
    the sizing model's flights are."""
    reserve = pack.soc_at_reserve(reserve_fraction)
    soc, time = 1.0, 0.0
    while soc > reserve + 1e-12:
        current = pack.current_for_power(soc, power_w)
        if current is None:
            break
        after = pack.drain(soc, current, dt)
        if after < reserve:
            time += (soc - reserve) * pack.capacity / current
            break
        soc, time = after, time + dt
    return time
