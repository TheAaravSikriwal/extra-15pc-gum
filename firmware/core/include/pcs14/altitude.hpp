// Altitude hold: the throttle stick asks for a climb rate, and centered it holds the height.
// GPL-3.0.
//
// Two loops, like PX4's: the height error asks for a vertical speed (MPC_Z_P), and the speed
// error asks for a vertical acceleration through a PI (MPC_Z_VEL_P_ACC, MPC_Z_VEL_I_ACC). The
// acceleration becomes a thrust from the drone's mass, divided by the tilt's cosine so leaning
// doesn't lose height. Down is positive throughout.
#pragma once

#include "pcs14/math.hpp"

namespace pcs14 {

struct AltitudeGains {
  float kp_height = 1.0f;     // 1/s
  float kp_speed = 4.0f;      // (m/s^2) per (m/s)
  float ki_speed = 2.0f;      // (m/s^2) per m
  float max_climb = 3.0f;     // m/s, at full stick
  float max_descent = 1.5f;   // m/s
  float max_accel = 5.0f;     // m/s^2 either way
  float deadband = 0.1f;      // of the stick's half travel, around center
  float max_tilt_cos = 0.5f;  // never boost thrust for tilt beyond 60 degrees
};

class AltitudeHold {
 public:
  explicit AltitudeHold(const AltitudeGains& gains = {}) : g_(gains) {}

  // starts holding where the drone is; at no error the thrust is the weight, so taking over
  // doesn't drop it
  void reset(float z);

  // the throttle stick (0 to 1, center holds), the height and its speed (down), the tilt's
  // cosine and the mass; returns the collective thrust in N
  float update(float stick, float z, float vz, float tilt_cos, float mass, float dt);

  // a climb rate asked for directly (m/s, down positive), as the automatic modes do; the
  // height setpoint follows it
  float update_speed(float vz_setpoint, float z, float vz, float tilt_cos, float mass,
                     float dt);
  // holds a height (z, down positive)
  float update_height(float z_setpoint, float z, float vz, float tilt_cos, float mass,
                      float dt);

  float z_setpoint() const { return z_sp_; }
  // the speed the stick asks for (m/s, down positive)
  float stick_speed(float stick) const;

 private:
  float thrust(float vz_sp, float vz, float tilt_cos, float mass, float dt);
  AltitudeGains g_;
  float z_sp_ = 0, integral_ = 0;
  bool holding_ = true;
};

}  // namespace pcs14
