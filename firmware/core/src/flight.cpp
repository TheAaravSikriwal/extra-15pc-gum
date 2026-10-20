// The flight loop. GPL-3.0.
#include "pcs14/flight.hpp"

namespace pcs14 {

Flight::Flight(const Airframe& airframe, const FlightGains& gains)
    : airframe_(airframe),
      gains_(gains),
      rate_{RateAxis(gains.roll), RateAxis(gains.pitch), RateAxis(gains.yaw)},
      mixer_(airframe.mixer) {}

void Flight::arm() {
  if (!armed_) {
    rate_.roll.reset();
    rate_.pitch.reset();
    rate_.yaw.reset();
  }
  armed_ = true;
}

void Flight::disarm() { armed_ = false; }

void Flight::on_mag(const Vec3& field) {
  mag_ = field;
  have_mag_ = true;
}

float Flight::hover_throttle() const { return airframe_.mass_kg * kG / max_thrust(); }

Mix Flight::step(const Vec3& gyro, const Vec3& accel, float dt) {
  attitude_.update(gyro, accel, have_mag_ ? &mag_ : nullptr, dt);
  have_mag_ = false;
  if (!armed_) {
    saturated_ = false;
    return Mix{};
  }
  const Vec3 rate = attitude_.rate();
  const Vec3 setpoint{clamp(sticks_.roll, -1, 1) * gains_.max_rate_roll_pitch,
                      clamp(sticks_.pitch, -1, 1) * gains_.max_rate_roll_pitch,
                      clamp(sticks_.yaw, -1, 1) * gains_.max_rate_yaw};
  const float throttle = clamp(sticks_.throttle, 0, 1);
  if (throttle < gains_.ground_throttle) {
    rate_.roll.reset();
    rate_.pitch.reset();
    rate_.yaw.reset();
  }
  const Vec3 accel_wanted = rate_.update(setpoint, rate, dt, saturated_);
  // torque = J a + w x (J w): the second part is the body's own gyroscopic coupling
  const Vec3& j = airframe_.inertia;
  const Vec3 jw{j.x * rate.x, j.y * rate.y, j.z * rate.z};
  const Vec3 torque =
      Vec3{j.x * accel_wanted.x, j.y * accel_wanted.y, j.z * accel_wanted.z} + rate.cross(jw);
  const Mix mix = mixer_.mix(torque, throttle * max_thrust());
  saturated_ = mix.saturated;
  return mix;
}

}  // namespace pcs14
