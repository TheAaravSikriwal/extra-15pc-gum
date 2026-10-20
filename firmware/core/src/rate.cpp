// The rate controller. GPL-3.0.
#include "pcs14/rate.hpp"

namespace pcs14 {

float RateAxis::update(float setpoint, float rate, float dt, bool saturated) {
  const float error = setpoint - rate;
  // the derivative of the measurement, low-passed
  float derivative = 0;
  if (have_last_ && dt > 0) {
    const float raw = (rate - last_rate_) / dt;
    const float rc = 1.0f / (2 * kPi * g_.d_cutoff_hz);
    d_filtered_ += (raw - d_filtered_) * dt / (rc + dt);
    derivative = d_filtered_;
  }
  last_rate_ = rate;
  have_last_ = true;
  if (!saturated) {
    integral_ = clamp(integral_ + g_.ki * error * dt, -g_.max_integral, g_.max_integral);
  }
  const float out = g_.kp * error + integral_ - g_.kd * derivative + g_.kff * setpoint;
  return clamp(out, -g_.max_out, g_.max_out);
}

}  // namespace pcs14
