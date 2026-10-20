// The attitude estimator. GPL-3.0.
#include "pcs14/attitude.hpp"

namespace pcs14 {

void Attitude::update(const Vec3& gyro, const Vec3& accel, const Vec3* mag, float dt) {
  Vec3 error{};
  // gravity: a still IMU feels the specific force pointing up, -z in the world frame
  const float g = accel.norm();
  if (g > (1 - gains_.accel_band) * kG && g < (1 + gains_.accel_band) * kG) {
    const Vec3 measured = (-accel).normalized();             // down, as the IMU sees it
    const Vec3 expected = q_.unrotate({0, 0, 1});             // down, as the estimate has it
    error += measured.cross(expected) * gains_.kp_accel;
  }
  // the field's horizontal part sets the heading; its vertical part says nothing new
  if (mag != nullptr && mag->norm() > 0) {
    const Vec3 world = q_.rotate(mag->normalized());
    const float horizontal = std::sqrt(world.x * world.x + world.y * world.y);
    const Vec3 reference = q_.unrotate({horizontal, 0, world.z});  // north, flattened
    const Vec3 measured = mag->normalized();
    // only the heading part of the error: project it onto the world's vertical, in the body
    const Vec3 down = q_.unrotate({0, 0, 1});
    const Vec3 heading_error = measured.cross(reference);
    error += down * (heading_error.dot(down) * gains_.kp_mag);
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
