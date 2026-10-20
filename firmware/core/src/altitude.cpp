// Altitude hold. GPL-3.0.
#include "pcs14/altitude.hpp"

#include <cmath>

namespace pcs14 {

void AltitudeHold::reset(float z) {
  z_sp_ = z;
  holding_ = true;
  integral_ = 0;
}

float AltitudeHold::stick_speed(float stick) const {
  const float s = clamp(stick, 0, 1) * 2 - 1;  // -1 to 1, center 0
  if (std::fabs(s) < g_.deadband) return 0;
  const float travel = (std::fabs(s) - g_.deadband) / (1 - g_.deadband);
  return s > 0 ? -travel * g_.max_climb : travel * g_.max_descent;  // up is minus down
}

float AltitudeHold::thrust(float vz_sp, float vz, float tilt_cos, float mass, float dt) {
  const float error = vz_sp - vz;
  float accel = g_.kp_speed * error + integral_;  // down positive
  const bool saturated = std::fabs(accel) > g_.max_accel;
  if (!saturated)
    integral_ = clamp(integral_ + g_.ki_speed * error * dt, -g_.max_accel, g_.max_accel);
  accel = clamp(accel, -g_.max_accel, g_.max_accel);
  // thrust pushes up (minus down): T cos(tilt) - m g = -m a
  return mass * (kG - accel) / std::fmax(tilt_cos, g_.max_tilt_cos);
}

float AltitudeHold::update(float stick, float z, float vz, float tilt_cos, float mass, float dt) {
  const float asked = stick_speed(stick);
  if (asked != 0) {
    holding_ = false;
    z_sp_ = z;  // follows the drone, so letting go holds where it is
    return thrust(asked, vz, tilt_cos, mass, dt);
  }
  if (!holding_) {
    holding_ = true;
    z_sp_ = z;
  }
  return update_height(z_sp_, z, vz, tilt_cos, mass, dt);
}

float AltitudeHold::update_speed(float vz_setpoint, float z, float vz, float tilt_cos,
                                 float mass, float dt) {
  z_sp_ = z;
  holding_ = false;
  return thrust(vz_setpoint, vz, tilt_cos, mass, dt);
}

float AltitudeHold::update_height(float z_setpoint, float z, float vz, float tilt_cos,
                                  float mass, float dt) {
  z_sp_ = z_setpoint;
  const float vz_sp = clamp(g_.kp_height * (z_setpoint - z), -g_.max_climb, g_.max_descent);
  return thrust(vz_sp, vz, tilt_cos, mass, dt);
}

}  // namespace pcs14
