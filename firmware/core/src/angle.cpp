// Self-levelling. GPL-3.0.
#include "pcs14/angle.hpp"

namespace pcs14 {

Vec3 angle_rates(const Quat& q, const Quat& setpoint, const AngleGains& g,
                 const Vec3& feed_forward) {
  Quat e = q.conjugate() * setpoint;  // the rotation still to go, in the body frame
  if (e.w < 0) e = {-e.w, -e.x, -e.y, -e.z};  // the short way round
  const Vec3 error{2 * e.x, 2 * e.y, 2 * e.z};
  Vec3 rates{error.x * g.kp_roll_pitch, error.y * g.kp_roll_pitch, error.z * g.kp_yaw};
  rates += feed_forward;
  return {clamp(rates.x, -g.max_rate_roll_pitch, g.max_rate_roll_pitch),
          clamp(rates.y, -g.max_rate_roll_pitch, g.max_rate_roll_pitch),
          clamp(rates.z, -g.max_rate_yaw, g.max_rate_yaw)};
}

Quat stick_attitude(float roll, float pitch, float yaw, float max_tilt) {
  return Quat::from_euler(clamp(roll, -1, 1) * max_tilt, clamp(pitch, -1, 1) * max_tilt, yaw);
}

}  // namespace pcs14
