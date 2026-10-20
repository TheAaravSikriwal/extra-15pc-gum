// The position filter and the position controller (step 5, task 8). GPL-3.0.
//
// The filter is the height filter's idea on the two horizontal axes: the accelerometer, turned
// into the world frame, carries the position and velocity from one sample to the next, and the
// GPS's position and velocity pull them back and teach it the accelerometer's bias. The
// vertical stays with the height filter (the barometer).
//
// The controller is PX4's shape (its MPC_XY_* and MPC_Z_* parameters): the position error asks
// for a velocity, the velocity error asks for an acceleration through a PID, and the
// acceleration, gravity taken off, is the thrust vector. Its direction is the attitude the
// drone needs and its length the collective thrust. Everything is north-east-down.
#pragma once

#include "pcs14/altitude.hpp"
#include "pcs14/math.hpp"

namespace pcs14 {

class PositionFilter {
 public:
  explicit PositionFilter(float crossover = 0.6f, float velocity_gain = 2.0f)
      : w_(crossover), kv_(velocity_gain) {}

  // the horizontal acceleration (m/s^2, world), from the accelerometer
  void predict(float accel_north, float accel_east, float dt);
  // a GPS fix: the position from home and the velocity, `dt` s after the last one
  void correct(float north, float east, float v_north, float v_east, float dt);

  float north() const { return p_[0]; }
  float east() const { return p_[1]; }
  float v_north() const { return v_[0]; }
  float v_east() const { return v_[1]; }
  bool valid() const { return valid_; }

 private:
  float w_, kv_;
  float p_[2]{}, v_[2]{}, bias_[2]{};
  bool valid_ = false;
};

struct PositionGains {
  float kp_position = 0.95f;  // 1/s, MPC_XY_P
  float kp_speed = 1.8f;      // (m/s^2) per (m/s), MPC_XY_VEL_P_ACC
  float ki_speed = 0.4f;      // MPC_XY_VEL_I_ACC
  float kd_speed = 0.2f;      // MPC_XY_VEL_D_ACC
  float max_speed = 12.0f;    // m/s, MPC_XY_VEL_MAX (the generator's parameters raise it)
  float max_tilt = 45.0f * kPi / 180;  // MPC_TILTMAX_AIR
  // m/s^2: how fast the horizontal velocity setpoint may change, so a jump in the setpoint
  // (a new point, a new mode) is a ramp the drone can follow (MPC_ACC_HOR_MAX)
  float max_setpoint_accel = 5.0f;
};

// what the automatic modes ask the position controller for
struct Setpoint {
  bool hold_xy = true;            // a position in the horizontal; otherwise a velocity
  float north = 0, east = 0;      // m from home, when holding
  float v_north = 0, v_east = 0;  // m/s: the velocity, or a feed-forward on top of the hold
  bool hold_z = true;             // a height; otherwise a vertical speed
  float z = 0, vz = 0;            // m and m/s, down positive
  float yaw = 0;                  // rad
};

// what the position controller asks of the attitude and the motors
struct Thrust {
  Quat attitude;     // the setpoint, body to north-east-down
  float thrust = 0;  // N
};

class PositionControl {
 public:
  explicit PositionControl(const PositionGains& xy = {}, const AltitudeGains& z = {})
      : g_(xy), z_(z) {}

  void reset();
  Thrust update(const Setpoint& sp, const Vec3& position, const Vec3& velocity, float mass,
                float dt);

 private:
  PositionGains g_;
  AltitudeGains z_;
  float integral_[3]{};
  float v_sp_[2]{};  // the slewed horizontal velocity setpoint
  Vec3 last_v_;
  bool have_last_ = false;
};

// a unit quaternion whose body down axis points along `down` (world) at the heading `yaw`
Quat attitude_from_down(const Vec3& down, float yaw);

}  // namespace pcs14
