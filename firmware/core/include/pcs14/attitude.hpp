// The attitude estimator: Mahony's complementary filter. GPL-3.0.
//
// The gyro carries the attitude from one sample to the next. Two slow corrections keep it
// honest: gravity, as the accelerometer feels it, pulls the tilt back toward the truth, and
// the magnetometer's horizontal part pulls the heading. Their error terms feed the gyro rate
// through a proportional gain (how fast it corrects) and an integral one (which learns the
// gyro's bias). The accelerometer is only trusted near 1 g: in a hard pull its direction says
// little about where down is.
//
// After R. Mahony, T. Hamel and J.-M. Pflimlin, "Nonlinear Complementary Filters on the Special
// Orthogonal Group", IEEE Transactions on Automatic Control 53(5), 2008.
#pragma once

#include "pcs14/math.hpp"

namespace pcs14 {

struct AttitudeGains {
  float kp_accel = 1.0f;  // 1/s: how hard gravity pulls the tilt back
  float kp_mag = 0.5f;    // 1/s: how hard the field pulls the heading
  float ki = 0.05f;       // 1/s^2: how fast it learns the gyro's bias
  float accel_band = 0.15f;  // the accelerometer counts within this share of 1 g
};

class Attitude {
 public:
  explicit Attitude(AttitudeGains gains = {}) : gains_(gains) {}

  void reset(const Quat& q) {
    q_ = q.normalized();
    bias_ = {};
  }

  // gyro in rad/s and accel in m/s^2 (specific force), both in the body frame; mag in any unit,
  // body frame, or nullptr when there's no new sample; dt in s. With `motion`, the drone's own
  // acceleration in the world frame (north-east-down, m/s^2, from the GPS's velocity), which
  // is taken out of the accelerometer first: while the drone speeds up sideways, what the
  // accelerometer feels is mostly the thrust, and without this the filter would drift toward
  // "level" while the drone leans
  void update(const Vec3& gyro, const Vec3& accel, const Vec3* mag, float dt,
              const Vec3* motion = nullptr);

  const Quat& q() const { return q_; }
  // rad/s: the gyro's bias as learned so far
  const Vec3& bias() const { return bias_; }
  // rad/s: the gyro with its bias taken out, as used by the last update
  const Vec3& rate() const { return rate_; }

 private:
  AttitudeGains gains_;
  Quat q_{};
  Vec3 bias_{};
  Vec3 rate_{};
};

}  // namespace pcs14
