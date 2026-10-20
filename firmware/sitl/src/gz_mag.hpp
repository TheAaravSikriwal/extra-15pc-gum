// Gazebo Harmonic's magnetometer, put right. GPL-3.0.
//
// Gazebo turns the field into the sensor's frame correctly, but the field it starts from is
// laid out wrong: the north-east-down numbers go into its east-north-up axes as (N, -E, D),
// a left-handed swap (gz-sim pull request 2460 fixes it in a later release). Measured
// 2026-10-20 on static models, level, pitched 30 degrees and rolled 30 degrees: the readings
// are that swapped field turned by the model's attitude, to four digits.
//
// Level, the swap is a fixed mapping, the one PX4's bridge uses: forward-right-down is
// (-y, -x, z). Tilted, it isn't: the swap doesn't commute with a tilt, so a fixed mapping
// gets the heading more wrong the more the drone leans (a quarter turn off in a 45 degree
// dash). Undoing it needs only the tilt, not the heading, because the swap does commute with a
// turn about the vertical; and the tilt comes from the accelerometer, not the magnetometer.
#pragma once

#include <cmath>

#include "pcs14/math.hpp"

namespace pcs14::sim {

// the true field in the body (forward-right-down), from Gazebo's reading (its own body frame,
// forward-left-up) and the attitude estimate (body forward-right-down to north-east-down)
inline Vec3 gazebo_magnetometer(const Vec3& reading_flu, const Quat& attitude_frd_ned) {
  // the estimate in Gazebo's frames (forward-left-up to east-north-up: half turns on each
  // side), then without its heading about Gazebo's vertical, which drops out of the swap
  const float s = std::sqrt(0.5f);
  const Quat enu_ned{0, s, s, 0}, frd_flu{0, 1, 0, 0};
  const Quat r = enu_ned * attitude_frd_ned * frd_flu;
  const Quat tilt = Quat::from_axis_angle({0, 0, 1}, -r.yaw()) * r;
  // into the (yaw-free) world, undo the swap there, and back into the body
  const Vec3 w = tilt.rotate(reading_flu);
  const Vec3 unswapped{-w.y, w.x, -w.z};
  const Vec3 b = tilt.unrotate(unswapped);
  return {b.x, -b.y, -b.z};  // forward-left-up to forward-right-down
}

}  // namespace pcs14::sim
