// The rate controller: one PID per axis, from body rates to angular accelerations. GPL-3.0.
//
// The controller asks for an angular acceleration (rad/s^2), not a unitless effort; the mixer
// multiplies it by the drone's inertia to get a torque. The gains then mean something
// physical, and the same gains suit every module combination, the inertia doing the rest.
//   out = kp e + ki (integral of e) - kd (filtered rate change) + kff setpoint
// The derivative works on the measured rate, not the error, so a stick step doesn't kick it;
// it's low-passed at `d_cutoff_hz`. The integrator is clamped and frozen while the mixer
// reports that the motors are saturated, so it can't wind up.
#pragma once

#include "pcs14/math.hpp"

namespace pcs14 {

struct RateGains {
  float kp;            // 1/s
  float ki;            // 1/s^2
  float kd;            // dimensionless (rad/s^2 per rad/s^2)
  float kff;           // 1/s
  float d_cutoff_hz;   // the derivative's low-pass
  float max_integral;  // rad/s^2
  float max_out;       // rad/s^2
};

class RateAxis {
 public:
  explicit RateAxis(RateGains gains) : g_(gains) {}

  // setpoint and rate in rad/s; `saturated` from the last mix. Returns rad/s^2.
  float update(float setpoint, float rate, float dt, bool saturated);

  void reset() {
    integral_ = 0;
    d_filtered_ = 0;
    have_last_ = false;
  }
  float integral() const { return integral_; }
  void set_gains(const RateGains& gains) { g_ = gains; }

 private:
  RateGains g_;
  float integral_{0};
  float last_rate_{0};
  float d_filtered_{0};
  bool have_last_{false};
};

// the three axes together
struct RateController {
  RateAxis roll, pitch, yaw;
  Vec3 update(const Vec3& setpoint, const Vec3& rate, float dt, bool saturated) {
    return {roll.update(setpoint.x, rate.x, dt, saturated),
            pitch.update(setpoint.y, rate.y, dt, saturated),
            yaw.update(setpoint.z, rate.z, dt, saturated)};
  }
};

}  // namespace pcs14
