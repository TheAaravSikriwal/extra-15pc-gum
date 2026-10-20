// The attitude estimator. GPL-3.0.
#include "pcs14/attitude.hpp"

namespace pcs14 {

void Attitude::update(const Vec3& gyro, const Vec3& accel_measured, const Vec3* mag, float dt,
                      const Vec3* motion) {
  Vec3 error{};
  // gravity: a still IMU feels the specific force pointing up, -z in the world frame; a
  // moving one feels its own acceleration on top, which comes out first when it's known
  const Vec3 accel = motion != nullptr ? accel_measured - q_.unrotate(*motion) : accel_measured;
  const float g = accel.norm();
  if (g > (1 - gains_.accel_band) * kG && g < (1 + gains_.accel_band) * kG) {
    const Vec3 measured = (-accel).normalized();             // down, as the IMU sees it
    const Vec3 expected = q_.unrotate({0, 0, 1});             // down, as the estimate has it
    error += measured.cross(expected) * gains_.kp_accel;
  }
  // the field's horizontal part sets the heading; its vertical part says nothing new. The
  // error is the angle between where the field points in the estimate's world and north, so
  // the pull doesn't fade with the field's dip (far north, its horizontal part is small)
  if (mag != nullptr && mag->norm() > 0) {
    const Vec3 world = q_.rotate(*mag);
    const float off = std::atan2(world.y, world.x);  // the field's heading, east of north
    if (!aligned_) {
      // the first sample sets the heading outright, as PX4 does when it starts
      q_ = (Quat::from_axis_angle({0, 0, 1}, -off) * q_).normalized();
      aligned_ = true;
    } else {
      error += q_.unrotate({0, 0, -off * gains_.kp_mag});
    }
  }
  // the bias is the integral of the error, the correction its proportional part
  bias_ -= error * (gains_.ki * dt);
  rate_ = gyro - bias_;
  const Vec3 w = rate_ + error;
  // integrate q' = q (0, w) / 2
  const Quat dq{0, w.x * 0.5f * dt, w.y * 0.5f * dt, w.z * 0.5f * dt};
  const Quat step = q_ * dq;
  q_ = Quat{q_.w + step.w, q_.x + step.x, q_.y + step.y, q_.z + step.z}.normalized();
}

}  // namespace pcs14
