// Self-levelling: from the attitude the drone should have to the body rates that get it there.
// GPL-3.0.
//
// The error between the attitude and its setpoint is a rotation; for small errors, twice its
// quaternion's vector part is the rotation vector in the body frame, and a proportional gain
// turns that into a rate setpoint for the rate loops. Yaw gets a softer gain than roll and
// pitch: tilting is what moves the drone, so it comes first. Like PX4's attitude controller
// (MC_ROLL_P, MC_PITCH_P, MC_YAW_P), without its split between the thrust axis and yaw.
#pragma once

#include "pcs14/math.hpp"

namespace pcs14 {

struct AngleGains {
  float kp_roll_pitch = 9.0f;  // 1/s, the flight sim's tuned PX4 value
  float kp_yaw = 2.8f;         // 1/s, PX4's default
  float max_rate_roll_pitch = 220.0f * kPi / 180;  // rad/s
  float max_rate_yaw = 200.0f * kPi / 180;
};

// rad/s body rates from the attitude `q` toward `setpoint`, plus `feed_forward` (body rates the
// setpoint itself is moving at, such as a yaw stick's turn)
Vec3 angle_rates(const Quat& q, const Quat& setpoint, const AngleGains& gains,
                 const Vec3& feed_forward = {});

// the attitude a pilot's sticks ask for in self-level: roll and pitch from -1 to 1 as angles
// up to `max_tilt` (rad), at the heading `yaw` (rad)
Quat stick_attitude(float roll, float pitch, float yaw, float max_tilt);

}  // namespace pcs14
