// The position filter and the position controller. GPL-3.0.
#include "pcs14/position.hpp"

#include <cmath>

namespace pcs14 {

void PositionFilter::predict(float accel_north, float accel_east, float dt) {
  if (!valid_) return;
  const float a[2] = {accel_north, accel_east};
  for (int k = 0; k < 2; ++k) {
    const float ak = a[k] - bias_[k];
    p_[k] += v_[k] * dt + 0.5f * ak * dt * dt;
    v_[k] += ak * dt;
  }
}

void PositionFilter::correct(float north, float east, float v_north, float v_east, float dt) {
  const float p[2] = {north, east}, v[2] = {v_north, v_east};
  if (!valid_) {
    for (int k = 0; k < 2; ++k) {
      p_[k] = p[k];
      v_[k] = v[k];
      bias_[k] = 0;
    }
    valid_ = true;
    return;
  }
  for (int k = 0; k < 2; ++k) {
    const float e = p[k] - p_[k];
    p_[k] += 3 * w_ * e * dt;
    v_[k] += 3 * w_ * w_ * e * dt + kv_ * (v[k] - v_[k]) * dt;
    bias_[k] -= w_ * w_ * w_ * e * dt;
  }
}

Quat attitude_from_down(const Vec3& down, float yaw) {
  const Vec3 z = down.normalized();
  const Vec3 heading{std::cos(yaw), std::sin(yaw), 0};
  Vec3 y = z.cross(heading);
  if (y.norm() < 1e-6f) y = {0, 1, 0};  // pointing straight along the heading: never in flight
  y = y.normalized();
  const Vec3 x = y.cross(z);
  // the rotation matrix's columns are the body axes in the world frame
  const float m00 = x.x, m01 = y.x, m02 = z.x;
  const float m10 = x.y, m11 = y.y, m12 = z.y;
  const float m20 = x.z, m21 = y.z, m22 = z.z;
  const float trace = m00 + m11 + m22;
  Quat q;
  if (trace > 0) {
    const float s = std::sqrt(trace + 1) * 2;
    q = {s / 4, (m21 - m12) / s, (m02 - m20) / s, (m10 - m01) / s};
  } else if (m00 > m11 && m00 > m22) {
    const float s = std::sqrt(1 + m00 - m11 - m22) * 2;
    q = {(m21 - m12) / s, s / 4, (m01 + m10) / s, (m02 + m20) / s};
  } else if (m11 > m22) {
    const float s = std::sqrt(1 + m11 - m00 - m22) * 2;
    q = {(m02 - m20) / s, (m01 + m10) / s, s / 4, (m12 + m21) / s};
  } else {
    const float s = std::sqrt(1 + m22 - m00 - m11) * 2;
    q = {(m10 - m01) / s, (m02 + m20) / s, (m12 + m21) / s, s / 4};
  }
  return q.normalized();
}

void PositionControl::reset() {
  integral_[0] = integral_[1] = integral_[2] = 0;
  have_last_ = false;
}

Thrust PositionControl::update(const Setpoint& sp, const Vec3& p, const Vec3& v, float mass,
                               float dt) {
  // the velocity setpoint
  Vec3 v_sp{sp.v_north, sp.v_east, sp.vz};
  if (sp.hold_xy) {
    v_sp.x += g_.kp_position * (sp.north - p.x);
    v_sp.y += g_.kp_position * (sp.east - p.y);
  }
  const float speed = std::sqrt(v_sp.x * v_sp.x + v_sp.y * v_sp.y);
  if (speed > g_.max_speed) {
    v_sp.x *= g_.max_speed / speed;
    v_sp.y *= g_.max_speed / speed;
  }
  // the slew: the setpoint follows what's asked at no more than max_setpoint_accel. It starts
  // from the drone's own velocity, so a new mode picks up where the drone is
  if (!have_last_) {
    v_sp_[0] = v.x;
    v_sp_[1] = v.y;
  }
  {
    const float dn = v_sp.x - v_sp_[0], de = v_sp.y - v_sp_[1];
    const float change = std::sqrt(dn * dn + de * de), step = g_.max_setpoint_accel * dt;
    const float share = change > step ? step / change : 1.0f;
    v_sp_[0] += dn * share;
    v_sp_[1] += de * share;
    v_sp.x = v_sp_[0];
    v_sp.y = v_sp_[1];
  }
  if (sp.hold_z) v_sp.z = z_.kp_height * (sp.z - p.z);
  v_sp.z = clamp(v_sp.z, -z_.max_climb, z_.max_descent);
  // the acceleration setpoint: a PID on the velocity, its derivative on the measurement
  Vec3 dv;
  if (have_last_ && dt > 0) dv = (v - last_v_) / dt;
  last_v_ = v;
  have_last_ = true;
  const float max_side = kG * std::tan(g_.max_tilt);
  const float kp[3] = {g_.kp_speed, g_.kp_speed, z_.kp_speed};
  const float ki[3] = {g_.ki_speed, g_.ki_speed, z_.ki_speed};
  const float kd[3] = {g_.kd_speed, g_.kd_speed, 0};
  const float lim[3] = {max_side, max_side, z_.max_accel};
  const float e[3] = {v_sp.x - v.x, v_sp.y - v.y, v_sp.z - v.z};
  const float d[3] = {dv.x, dv.y, dv.z};
  float a[3];
  for (int k = 0; k < 3; ++k) {
    a[k] = kp[k] * e[k] + integral_[k] - kd[k] * d[k];
    if (std::fabs(a[k]) < lim[k])  // no wind-up while saturated
      integral_[k] = clamp(integral_[k] + ki[k] * e[k] * dt, -lim[k], lim[k]);
    a[k] = clamp(a[k], -lim[k], lim[k]);
  }
  // keep the sideways part inside the tilt limit, as one vector
  const float side = std::sqrt(a[0] * a[0] + a[1] * a[1]);
  const float lift = kG - a[2];  // what the thrust has to give upward, per kg
  const float side_max = std::fmax(lift, 0.1f) * std::tan(g_.max_tilt);
  if (side > side_max) {
    a[0] *= side_max / side;
    a[1] *= side_max / side;
  }
  // thrust = m (a - g), and the body's down axis points against it
  const Vec3 force{mass * a[0], mass * a[1], mass * (a[2] - kG)};
  Thrust out;
  out.thrust = force.norm();
  out.attitude = attitude_from_down(-force, sp.yaw);
  return out;
}

}  // namespace pcs14
