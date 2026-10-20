"""Gazebo's multicopter motor model, fitted to this build's motor and prop.

Gazebo makes each rotor's thrust motorConstant x w^2 and its drag torque momentConstant x the
thrust, with the rotor's speed chasing its command through a first-order lag (timeConstantUp
and timeConstantDown), up to maxRotVelocity. The numbers come from:

- motorConstant: a least-squares fit, through zero, of the motor's thrust table against w^2,
  with the thrust derated the way the sizing model's pessimistic case does it. Real props aren't
  exactly w^2, so the fit only uses the rows where the drone flies, from a little under its
  hover to a little over its top speed
- momentConstant: each row's shaft torque (its electrical power, times the sizing model's motor
  and ESC efficiency, over w) over its thrust, averaged
- maxRotVelocity: the speed at which the fitted motor makes the sizing model's full-throttle
  thrust, the pessimistic rotor on the pack at its 20% reserve, held to the firmware's current
  cap. Every scenario flies on that worst case (the flight sim spec, "the battery and my 90 A
  cap"). It matches the thrust rather than the sizing model's rpm, because that rpm comes from
  a power law anchored on the table's top row, which sits about 5% off the table in mid-range;
  thrust is what decides thrust-to-weight, top speed and the wind hold
- the props' in-plane drag, their rolling moment and the motors' spin-up and spin-down times,
  which no table gives: PX4's x500 values, flagged as estimates

The model flies the drone as built: its mass is the CAD's, without the sizing model's growth
margin, which is room for later parts rather than weight the drone carries today.
"""

import math
from dataclasses import dataclass

# PX4's x500 (models/x500/model.sdf in PX4-gazebo-models, at commit b6127f4, which PX4 v1.17.0
# pins as its Tools/simulation/gz submodule)
X500 = {
    "time_constant_up": 0.0125,  # s
    "time_constant_down": 0.025,  # s
    "rotor_drag_coefficient": 8.06428e-05,
    "rolling_moment_coefficient": 1e-06,
}
X500_SOURCE = "PX4's x500 model (PX4-gazebo-models b6127f4, pinned by PX4 v1.17.0)"
G = 9.80665
MOTORS = 4
FIT_BELOW = 0.8  # the fit's rows: from this share of the hover speed...
FIT_ABOVE = 1.2  # ...to this share of the top speed


def rad_s(rpm: float) -> float:
    return rpm * 2 * math.pi / 60


def fit_motor_constant(omegas, thrusts) -> float:
    """k in thrust = k w^2, the least-squares line through zero."""
    squares = [w**2 for w in omegas]
    return sum(s * t for s, t in zip(squares, thrusts, strict=True)) / sum(s * s for s in squares)


def fit_moment_constant(omegas, thrusts, powers, efficiency: float) -> float:
    """Drag torque over thrust, averaged over the rows: torque = efficiency x power / w."""
    ratios = [
        efficiency * p / w / t for w, t, p in zip(omegas, thrusts, powers, strict=True) if t > 0
    ]
    return sum(ratios) / len(ratios)


@dataclass(frozen=True)
class MotorModel:
    motor_constant: float  # N / (rad/s)^2
    moment_constant: float  # m
    max_rot_velocity: float  # rad/s
    hover_rot_velocity: float  # rad/s, for this setup's mass
    time_constant_up: float  # s
    time_constant_down: float  # s
    rotor_drag_coefficient: float
    rolling_moment_coefficient: float
    estimates: tuple[str, ...]  # the fields that aren't fitted to this build's data
    estimate_note: str


def motor_model(build, targets, setup, mass: float) -> MotorModel:
    """The motor model for one setup, flying at `mass` kg (the CAD's, with any payload)."""
    from pcs14.sizing.battery import Pack
    from pcs14.sizing.flight import power_model
    from pcs14.sizing.rotor import Rotor

    rotor = Rotor.from_build(build, pessimistic=True)
    full = rotor.full_throttle(Pack(build.pack), targets.reserve_fraction)
    hover_rpm = rotor.rpm_for_thrust(mass * G / MOTORS)
    if hover_rpm is None:
        raise ValueError("the thrust table has no rpm column, so the motor model can't be fitted")
    rows = [r for r in rotor.table.rows if r.rpm]
    flown = [r for r in rows if FIT_BELOW * hover_rpm <= r.rpm <= FIT_ABOVE * full.rpm]
    rows = flown if len(flown) >= 2 else rows
    omegas = [rad_s(r.rpm) for r in rows]
    thrusts = [r.thrust * rotor.thrust_scale for r in rows]
    k = fit_motor_constant(omegas, thrusts)
    efficiency = power_model(build, setup, 0.0, pessimistic=True).efficiency
    kappa = fit_moment_constant(omegas, thrusts, [r.power for r in rows], efficiency)
    return MotorModel(
        motor_constant=k,
        moment_constant=kappa,
        max_rot_velocity=math.sqrt(full.thrust / k),
        hover_rot_velocity=rad_s(hover_rpm),
        estimates=tuple(X500),
        estimate_note=X500_SOURCE,
        **X500,
    )
