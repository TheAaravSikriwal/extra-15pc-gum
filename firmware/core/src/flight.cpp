// The flight loop. GPL-3.0.
#include "pcs14/flight.hpp"

#include <cmath>

namespace pcs14 {

Flight::Flight(const Airframe& airframe, const FlightGains& gains)
    : airframe_(airframe),
      gains_(gains),
      height_(gains.height_crossover),
      altitude_(gains.altitude),
      rate_{RateAxis(gains.roll), RateAxis(gains.pitch), RateAxis(gains.yaw)},
      mixer_(airframe.mixer) {}

void Flight::reset_integrators() {
  rate_.roll.reset();
  rate_.pitch.reset();
  rate_.yaw.reset();
}

void Flight::arm() {
  if (!armed_) {
    reset_integrators();
    yaw_setpoint_ = attitude_.q().yaw();
    takeoff_z_ = height_.z();
    altitude_.reset(height_.z());
    flown_ = false;
  }
  armed_ = true;
}

void Flight::disarm() { armed_ = false; }

bool Flight::set_mode(Mode mode) {
  if (mode != Mode::Acro && mode != Mode::Manual && mode != Mode::Altitude) return false;
  if (mode != mode_) {
    yaw_setpoint_ = attitude_.q().yaw();
    altitude_.reset(height_.z());
  }
  mode_ = mode;
  return true;
}

void Flight::on_mag(const Vec3& field) {
  mag_ = field;
  have_mag_ = true;
}

void Flight::on_baro(float pressure_pa, float dt) {
  if (reference_pa_ <= 0) {
    reference_pa_ = pressure_pa;  // heights are from where it started
    return;
  }
  height_.correct(-pressure_height(pressure_pa, reference_pa_), dt);
}

void Flight::on_gps_velocity(const Vec3& velocity, float dt) {
  if (have_gps_velocity_ && dt > 0) {
    const Vec3 accel = (velocity - gps_velocity_) / dt;
    motion_ += (accel - motion_) * (dt / (gains_.motion_smoothing_s + dt));
  }
  gps_velocity_ = velocity;
  have_gps_velocity_ = true;
}

float Flight::hover_throttle() const { return airframe_.mass_kg * kG / max_thrust(); }

bool Flight::on_ground() const {
  if (mode_ == Mode::Acro) return !armed_ || sticks_.throttle < gains_.ground_throttle;
  return land_.landed();
}

Mix Flight::step(const Vec3& gyro, const Vec3& accel, float dt) {
  attitude_.update(gyro, accel, have_mag_ ? &mag_ : nullptr, dt,
                   have_gps_velocity_ ? &motion_ : nullptr);
  have_mag_ = false;
  const Quat& q = attitude_.q();
  height_.predict(q.rotate(accel).z, dt);
  if (!armed_) {
    saturated_ = false;
    land_.update(false, 0, height_.vz(), 0, dt);
    return Mix{};
  }
  const Vec3 rate = attitude_.rate();
  const float throttle = clamp(sticks_.throttle, 0, 1);
  const float yaw_rate = clamp(sticks_.yaw, -1, 1) * gains_.max_rate_yaw;
  const float mass = airframe_.mass_kg;
  Vec3 rate_sp;
  float thrust;
  bool on_ground_idle = false;
  if (mode_ == Mode::Acro) {
    rate_sp = {clamp(sticks_.roll, -1, 1) * gains_.max_rate_roll_pitch,
               clamp(sticks_.pitch, -1, 1) * gains_.max_rate_roll_pitch, yaw_rate};
    thrust = throttle * max_thrust();
    on_ground_idle = throttle < gains_.ground_throttle;
  } else {
    yaw_setpoint_ = wrap_pi(yaw_setpoint_ + yaw_rate * dt);
    const Quat q_sp =
        stick_attitude(sticks_.roll, sticks_.pitch, yaw_setpoint_, gains_.max_tilt);
    rate_sp = angle_rates(q, q_sp, gains_.angle, {0, 0, yaw_rate});
    const float tilt_cos = std::cos(q.tilt());
    if (mode_ == Mode::Manual) {
      thrust = throttle * max_thrust();
      on_ground_idle = land_.landed() && throttle < gains_.ground_throttle;
    } else {
      // on the ground, altitude mode waits for the stick to ask for a climb
      if (land_.landed() && altitude_.stick_speed(throttle) >= 0) {
        on_ground_idle = true;
        altitude_.reset(height_.z());
        thrust = 0;
      } else {
        thrust = altitude_.update(throttle, height_.z(), height_.vz(), tilt_cos, mass, dt);
      }
    }
  }
  if (on_ground_idle) {
    reset_integrators();
    yaw_setpoint_ = q.yaw();
  }
  const Vec3 accel_wanted = rate_.update(rate_sp, rate, dt, saturated_);
  // torque = J a + w x (J w): the second part is the body's own gyroscopic coupling
  const Vec3& j = airframe_.inertia;
  const Vec3 jw{j.x * rate.x, j.y * rate.y, j.z * rate.z};
  const Vec3 torque =
      Vec3{j.x * accel_wanted.x, j.y * accel_wanted.y, j.z * accel_wanted.z} + rate.cross(jw);
  const Mix mix = mixer_.mix(torque, thrust);
  saturated_ = mix.saturated;
  float total = 0;
  for (float t : mix.thrust) total += t;
  land_.update(true, total / (mass * kG), height_.vz(), takeoff_z_ - height_.z(), dt);
  if (!land_.landed()) flown_ = true;
  const float wait = flown_ ? gains_.disarm_after_landing_s : gains_.disarm_before_takeoff_s;
  if (mode_ != Mode::Acro && land_.landed() && land_.landed_for() > wait) disarm();
  return mix;
}

}  // namespace pcs14
