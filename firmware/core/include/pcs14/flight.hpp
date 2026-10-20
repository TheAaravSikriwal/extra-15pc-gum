// The flight loop: one IMU sample in, four motor speeds out. GPL-3.0.
//
// The modes (step 5, tasks 4, 7 and 8):
// - Acro, rate mode: the sticks ask for body rates; the throttle is the thrust
// - Manual, self-level: the sticks ask for tilt angles and a yaw rate; the throttle is the thrust
// - Altitude: self-level, and the throttle stick asks for a climb rate, holding the height
//   when centered
// - Position: the sticks ask for velocities, and centered it holds the spot
// - Takeoff: climbs to the take-off height over where it armed, then holds (PX4's AUTO_TAKEOFF)
// - Hold: holds where it was when it switched (AUTO_LOITER)
// - Land: comes straight down, slowing near the ground, and disarms (AUTO_LAND)
// - Return: climbs to the return height, flies home and lands (AUTO_RTL)
// - Offboard: flies the setpoints the companion computer (or a script) streams
// Underneath every mode: the rate loops turn rate errors into angular accelerations, the
// airframe's inertia turns those into torques, and the mixer turns torques and thrust into
// motor speeds. The attitude estimator, the height filter and the position filter run all the
// time, and the land detector disarms the drone two seconds after it lands, like PX4.
#pragma once

#include "pcs14/altitude.hpp"
#include "pcs14/angle.hpp"
#include "pcs14/attitude.hpp"
#include "pcs14/height.hpp"
#include "pcs14/land.hpp"
#include "pcs14/limits.hpp"
#include "pcs14/mixer.hpp"
#include "pcs14/modes.hpp"
#include "pcs14/position.hpp"
#include "pcs14/rate.hpp"

namespace pcs14 {

// what the drone is, in the body frame (forward-right-down) about its center of gravity
struct Airframe {
  float mass_kg = 0;
  Vec3 inertia;  // kg m^2: the diagonal; the cross terms are small on a symmetric quad
  MixerSetup mixer;
  // for the current cap's estimate (0: no estimate, no cap): a motor's power is
  // power_coefficient * speed^power_exponent; the pack's voltage; the avionics' power
  float power_coefficient = 0, power_exponent = 3, pack_volts = 0, avionics_w = 0;
};

struct FlightGains {
  // The integrator is what holds an off-center weight in rate mode, and the tilt the drone
  // picks up before it catches up is about the weight's pull (rad/s^2) over ki: 3 mm off
  // center is 4.4 rad/s^2 on base, so 2.5 degrees at ki 100, against 6 at 40.
  RateGains roll{20.0f, 100.0f, 0.5f, 0.0f, 40.0f, 400.0f, 400.0f};
  RateGains pitch{20.0f, 100.0f, 0.5f, 0.0f, 40.0f, 400.0f, 400.0f};
  RateGains yaw{8.0f, 8.0f, 0.0f, 0.0f, 40.0f, 50.0f, 100.0f};
  AngleGains angle;
  AltitudeGains altitude;
  PositionGains position;
  float max_rate_roll_pitch = 220.0f * kPi / 180;  // rad/s at full stick, in rate mode
  float max_rate_yaw = 200.0f * kPi / 180;         // rad/s at full stick, in every mode
  float max_tilt = 35.0f * kPi / 180;              // rad at full stick, self-levelling
  // below this throttle the drone is taken to be on the ground in rate mode: the integrators
  // stay at zero, so they don't wind up against the ground before take-off
  float ground_throttle = 0.15f;
  float disarm_after_landing_s = 2.0f;    // PX4's COM_DISARM_LAND
  float disarm_before_takeoff_s = 10.0f;  // armed and never taken off: PX4's COM_DISARM_PRFLT
  float motion_smoothing_s = 0.2f;        // the low-pass on the GPS's acceleration
  float height_crossover = 1.0f;  // rad/s: where the height filter hands over to the barometer
};

// the automatic modes' settings, PX4's parameters by name and default
struct AutoSettings {
  float takeoff_height = 2.5f;   // m, MIS_TAKEOFF_ALT
  float takeoff_speed = 1.5f;    // m/s, MPC_TKO_SPEED
  float climb_speed = 3.0f;      // m/s, MPC_Z_V_AUTO_UP
  float descent_speed = 1.5f;    // m/s, MPC_Z_V_AUTO_DN
  float land_speed = 0.7f;       // m/s, MPC_LAND_SPEED, below land_slow_height
  float land_slow_height = 10.0f;  // m, MPC_LAND_ALT1: where landing starts to slow down
  float land_slowest_height = 5.0f;  // m, MPC_LAND_ALT2: at the land speed from here down
  float cruise_speed = 5.0f;     // m/s, MPC_XY_CRUISE
  float manual_speed = 10.0f;    // m/s at full stick in position mode, MPC_VEL_MANUAL
  float return_height = 60.0f;   // m over home, RTL_RETURN_ALT
  float offboard_loss_s = 1.0f;  // s without a setpoint before offboard holds, COM_OF_LOSS_T
};

// the pilot's sticks: roll, pitch and yaw from -1 to 1 (right, nose up, nose right), throttle
// from 0 to 1
struct Sticks {
  float roll = 0, pitch = 0, yaw = 0, throttle = 0;
};

// an offboard setpoint: a position (with an optional velocity on top) or a velocity, and a
// heading, north-east-down from where the filters started
struct OffboardTarget {
  bool position = true;  // a position; otherwise a velocity
  Vec3 point, velocity;
  float yaw = 0;
};

class Flight {
 public:
  explicit Flight(const Airframe& airframe, const FlightGains& gains = {});

  void arm();
  void disarm();
  bool armed() const { return armed_; }
  // switches mode; false (staying put) for one it can't fly now (the automatic modes need a
  // position, and taking off needs to be armed and on the ground)
  bool set_mode(Mode mode);
  Mode mode() const { return mode_; }
  void set_sticks(const Sticks& sticks) { sticks_ = sticks; }
  void set_auto(const AutoSettings& settings) { auto_ = settings; }
  // new gains, taking effect at the next step (live tuning from the ground station); the
  // integrators keep what they've learned
  void set_tuning(const FlightGains& gains);
  const FlightGains& gains() const { return gains_; }
  // an offboard setpoint, at `t` s (the flight loop's own clock: the sum of its steps)
  void set_offboard(const OffboardTarget& target);
  // a magnetometer sample, body frame, any unit; used by the next step
  void on_mag(const Vec3& field);
  // a barometer sample, Pa, `dt` s after the last one
  void on_baro(float pressure_pa, float dt);
  // a GPS fix: the position north and east of where the GPS first had a fix, and the velocity
  // (north-east-down), `dt` s after the last one
  void on_gps(float north, float east, const Vec3& velocity, float dt);
  // just the GPS's velocity, for the attitude estimator (the rate and self-level tests)
  void on_gps_velocity(const Vec3& velocity, float dt);

  // flight termination: the motors stop and stay stopped (the chute is the bridge's to fire)
  void terminate();
  bool terminated() const { return mode_ == Mode::Termination; }
  // a motor that has failed (0 to 3): its output stays at zero, as PX4's failure injection does
  void fail_motor(int index);
  // the motors' top speed, lowered (a sagging pack) or back to their own
  void set_max_rad_s(float max_rad_s) { mixer_.set_max_rad_s(max_rad_s); }
  // stops (or restarts) using the GPS, as PX4's EKF2_GPS_CTRL does; a second without it and the
  // position is no longer valid
  void use_gps(bool use) { use_gps_ = use; }
  // the highest an automatic setpoint may go, in m over home (the limits profile's ceiling and
  // the parachute rule; pcs14/limits.hpp)
  void set_height_limit(float m) { height_limit_ = m; }
  // the battery current the motors are estimated to draw (A), and what the cap allows
  float current() const { return current_; }
  float current_allowed() const { return current_allowed_; }
  const CurrentCap& current_cap() const { return cap_; }

  // one control step: gyro (rad/s) and accelerometer (m/s^2, specific force), body frame.
  // Returns the motors' speeds: zero when disarmed, idle or more when armed.
  Mix step(const Vec3& gyro, const Vec3& accel, float dt);

  const Attitude& attitude() const { return attitude_; }
  const Sticks& sticks() const { return sticks_; }
  // the estimate: position (north, east from the GPS's first fix; down from where the
  // barometer started) and velocity, north-east-down
  Vec3 position() const { return {position_.north(), position_.east(), height_.z()}; }
  Vec3 velocity() const { return {position_.v_north(), position_.v_east(), height_.vz()}; }
  bool position_valid() const { return position_.valid() && t_ - gps_t_ < kGpsTimeout; }
  float z() const { return height_.z(); }
  float vz() const { return height_.vz(); }
  // where it armed, the home it returns to
  const Vec3& home() const { return home_; }
  bool home_valid() const { return home_set_; }
  // whether it's on the ground, by the land detector; in rate mode, by the throttle as well
  bool on_ground() const;
  // the throttle whose thrust carries the drone's weight
  float hover_throttle() const;
  float max_thrust() const { return 4 * mixer_.max_thrust(); }

 private:
  void reset_integrators();
  void enter(Mode mode);
  Setpoint automatic(float dt, bool& done);
  Airframe airframe_;
  FlightGains gains_;
  AutoSettings auto_;
  Attitude attitude_;
  HeightFilter height_;
  PositionFilter position_;
  AltitudeHold altitude_;
  PositionControl control_;
  LandDetector land_;
  RateController rate_;
  Mixer mixer_;
  Mode mode_ = Mode::Acro;
  Sticks sticks_;
  OffboardTarget offboard_;
  float offboard_t_ = -1e9f;
  float t_ = 0;  // s: the loop's own clock
  Vec3 mag_;
  float reference_pa_ = 0;
  float yaw_setpoint_ = 0;
  float takeoff_z_ = 0;
  Vec3 home_;
  bool home_set_ = false;
  Setpoint hold_;    // where the automatic modes hold, and land from
  int phase_ = 0;    // the steps of take-off and return
  Vec3 gps_velocity_, motion_;
  bool have_gps_velocity_ = false;
  bool flown_ = false;  // taken off since it armed
  bool use_gps_ = true;
  float height_limit_ = 1e9f;
  CurrentCap cap_;
  float current_ = 0, current_allowed_ = 1e9f;
  float gps_t_ = -1e9f;  // when the GPS was last used
  bool failed_[4]{};
  static constexpr float kGpsTimeout = 1.0f;  // s
  bool have_mag_ = false;
  bool armed_ = false;
  bool saturated_ = false;
};

}  // namespace pcs14
