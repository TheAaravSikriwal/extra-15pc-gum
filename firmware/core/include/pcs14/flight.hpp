// The flight loop: one IMU sample in, four motor speeds out. GPL-3.0.
//
// Rate mode for now (step 5, task 4): the sticks ask for body rates, the rate loops turn the
// rate error into angular accelerations, the airframe's inertia turns those into torques, and
// the mixer turns torques and the throttle's thrust into motor speeds. The attitude estimator
// runs alongside, so the angle modes have it when they come.
#pragma once

#include "pcs14/attitude.hpp"
#include "pcs14/mixer.hpp"
#include "pcs14/rate.hpp"

namespace pcs14 {

// what the drone is, in the body frame (forward-right-down) about its center of gravity
struct Airframe {
  float mass_kg = 0;
  Vec3 inertia;  // kg m^2: the diagonal; the cross terms are small on a symmetric quad
  MixerSetup mixer;
};

struct FlightGains {
  // The integrator is what holds an off-center weight in rate mode, and the tilt the drone
  // picks up before it catches up is about the weight's pull (rad/s^2) over ki: 3 mm off
  // center is 4.4 rad/s^2 on base, so 2.5 degrees at ki 100, against 6 at 40.
  RateGains roll{20.0f, 100.0f, 0.5f, 0.0f, 40.0f, 400.0f, 400.0f};
  RateGains pitch{20.0f, 100.0f, 0.5f, 0.0f, 40.0f, 400.0f, 400.0f};
  RateGains yaw{8.0f, 8.0f, 0.0f, 0.0f, 40.0f, 50.0f, 100.0f};
  float max_rate_roll_pitch = 220.0f * kPi / 180;  // rad/s at full stick
  float max_rate_yaw = 200.0f * kPi / 180;
  // below this throttle the drone is taken to be on the ground: the integrators stay at zero,
  // so they don't wind up against the ground before take-off
  float ground_throttle = 0.15f;
};

// the pilot's sticks: roll, pitch and yaw from -1 to 1 (right, nose up, nose right), throttle
// from 0 to 1
struct Sticks {
  float roll = 0, pitch = 0, yaw = 0, throttle = 0;
};

class Flight {
 public:
  explicit Flight(const Airframe& airframe, const FlightGains& gains = {});

  void arm();
  void disarm();
  bool armed() const { return armed_; }
  void set_sticks(const Sticks& sticks) { sticks_ = sticks; }
  // a magnetometer sample, body frame, any unit; used by the next step
  void on_mag(const Vec3& field);

  // one control step: gyro (rad/s) and accelerometer (m/s^2, specific force), body frame.
  // Returns the motors' speeds: zero when disarmed, idle or more when armed.
  Mix step(const Vec3& gyro, const Vec3& accel, float dt);

  const Attitude& attitude() const { return attitude_; }
  const Sticks& sticks() const { return sticks_; }
  // whether it's on the ground: disarmed, or armed with the throttle under the ground
  // throttle. A stand-in until the land detector comes with altitude hold (task 7).
  bool on_ground() const { return !armed_ || sticks_.throttle < gains_.ground_throttle; }
  // the throttle whose thrust carries the drone's weight
  float hover_throttle() const;
  float max_thrust() const { return 4 * mixer_.max_thrust(); }

 private:
  Airframe airframe_;
  FlightGains gains_;
  Attitude attitude_;
  RateController rate_;
  Mixer mixer_;
  Sticks sticks_;
  Vec3 mag_;
  bool have_mag_ = false;
  bool armed_ = false;
  bool saturated_ = false;
};

}  // namespace pcs14
