// The flight loop. GPL-3.0.
#include "pcs14/flight.hpp"

#include <cmath>

namespace pcs14 {

namespace {
bool needs_position(Mode m) {
  return m == Mode::Position || m == Mode::Takeoff || m == Mode::Hold || m == Mode::Land ||
         m == Mode::Return || m == Mode::Offboard;
}
constexpr float kReached = 0.3f;  // m: close enough to a take-off height
constexpr float kHome = 1.0f;     // m: close enough to home to start down
}  // namespace

Flight::Flight(const Airframe& airframe, const FlightGains& gains)
    : airframe_(airframe),
      gains_(gains),
      height_(gains.height_crossover),
      altitude_(gains.altitude),
      control_(gains.position, gains.altitude),
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
    control_.reset();
    yaw_setpoint_ = attitude_.q().yaw();
    takeoff_z_ = height_.z();
    altitude_.reset(height_.z());
    flown_ = false;
    home_ = position();
    home_set_ = position_.valid();
    enter(mode_);
  }
  armed_ = true;
}

void Flight::disarm() { armed_ = false; }

void Flight::enter(Mode mode) {
  mode_ = mode;
  phase_ = 0;
  yaw_setpoint_ = attitude_.q().yaw();
  altitude_.reset(height_.z());
  hold_ = Setpoint{};
  hold_.north = position_.north();
  hold_.east = position_.east();
  hold_.z = height_.z();
  hold_.yaw = yaw_setpoint_;
}

bool Flight::set_mode(Mode mode) {
  if (mode == Mode::Termination) return false;  // its own command, in task 9
  if (needs_position(mode) && !position_.valid()) return false;
  if (mode == Mode::Takeoff && !(armed_ && land_.landed())) return false;
  if (mode == Mode::Return && !home_set_) return false;
  if (mode == Mode::Offboard && t_ - offboard_t_ > auto_.offboard_loss_s) return false;
  if (mode != mode_) enter(mode);
  return true;
}

void Flight::set_offboard(const OffboardTarget& target) {
  offboard_ = target;
  offboard_t_ = t_;
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

void Flight::on_gps(float north, float east, const Vec3& velocity, float dt) {
  position_.correct(north, east, velocity.x, velocity.y, dt);
  on_gps_velocity(velocity, dt);
}

float Flight::hover_throttle() const { return airframe_.mass_kg * kG / max_thrust(); }

bool Flight::on_ground() const {
  if (mode_ == Mode::Acro) return !armed_ || sticks_.throttle < gains_.ground_throttle;
  return land_.landed();
}

// the automatic modes' setpoints; `done` when take-off is finished
Setpoint Flight::automatic(float, bool& done) {
  done = false;
  Setpoint sp = hold_;
  const Vec3 p = position();
  switch (mode_) {
    case Mode::Takeoff: {
      const float target = takeoff_z_ - auto_.takeoff_height;
      if (phase_ == 0) {
        sp.hold_z = false;
        sp.vz = -auto_.takeoff_speed;
        if (p.z <= target + kReached) phase_ = 1;
      } else {
        sp.z = target;
        done = std::fabs(p.z - target) < kReached && std::fabs(height_.vz()) < 0.3f;
      }
      break;
    }
    case Mode::Land:
    case Mode::Return: {
      if (mode_ == Mode::Return && phase_ == 0) {  // up to the return height first
        sp.z = std::fmin(p.z, home_.z - auto_.return_height);
        hold_.z = sp.z;
        if (p.z <= sp.z + 1.0f) phase_ = 1;
        break;
      }
      if (mode_ == Mode::Return && phase_ == 1) {  // home, at the cruise speed
        const float dn = home_.x - p.x, de = home_.y - p.y;
        const float distance = std::sqrt(dn * dn + de * de);
        if (distance < kHome) {
          phase_ = 2;
          hold_.north = home_.x;
          hold_.east = home_.y;
        } else {
          const float speed = std::fmin(auto_.cruise_speed, 0.95f * distance);
          sp.hold_xy = false;
          sp.v_north = dn / distance * speed;
          sp.v_east = de / distance * speed;
        }
        sp.z = hold_.z;
        break;
      }
      // coming down: fast up high, slowing to the land speed near the ground
      const float height = home_set_ ? home_.z - p.z : takeoff_z_ - p.z;
      const float span = auto_.land_slow_height - auto_.land_slowest_height;
      const float share = clamp((height - auto_.land_slowest_height) / span, 0, 1);
      sp.hold_z = false;
      sp.vz = auto_.land_speed + share * (auto_.descent_speed - auto_.land_speed);
      break;
    }
    case Mode::Offboard: {
      if (t_ - offboard_t_ > auto_.offboard_loss_s) break;  // stale: hold (failsafes: task 9)
      const OffboardTarget& o = offboard_;
      sp.yaw = o.yaw;
      if (o.position) {
        sp.north = o.point.x;
        sp.east = o.point.y;
        sp.z = o.point.z;
        sp.v_north = o.velocity.x;
        sp.v_east = o.velocity.y;
      } else {
        sp.hold_xy = sp.hold_z = false;
        sp.v_north = o.velocity.x;
        sp.v_east = o.velocity.y;
        sp.vz = o.velocity.z;
      }
      hold_ = sp;  // where it stays if the setpoints stop
      hold_.hold_xy = hold_.hold_z = true;
      hold_.north = p.x;
      hold_.east = p.y;
      hold_.z = o.position ? o.point.z : p.z;
      break;
    }
    default:  // Hold
      break;
  }
  return sp;
}

Mix Flight::step(const Vec3& gyro, const Vec3& accel, float dt) {
  t_ += dt;
  attitude_.update(gyro, accel, have_mag_ ? &mag_ : nullptr, dt,
                   have_gps_velocity_ ? &motion_ : nullptr);
  have_mag_ = false;
  const Quat& q = attitude_.q();
  const Vec3 world = q.rotate(accel);  // the specific force: horizontally, the acceleration
  height_.predict(world.z, dt);
  position_.predict(world.x, world.y, dt);
  if (!armed_) {
    saturated_ = false;
    land_.update(false, 0, height_.vz(), 0, dt);
    return Mix{};
  }
  const Vec3 rate = attitude_.rate();
  const float throttle = clamp(sticks_.throttle, 0, 1);
  const float yaw_rate = clamp(sticks_.yaw, -1, 1) * gains_.max_rate_yaw;
  const float mass = airframe_.mass_kg;
  const float tilt_cos = std::cos(q.tilt());
  Vec3 rate_sp;
  float thrust = 0;
  bool idle = false;  // on the ground and not asked to leave it
  if (mode_ == Mode::Acro) {
    rate_sp = {clamp(sticks_.roll, -1, 1) * gains_.max_rate_roll_pitch,
               clamp(sticks_.pitch, -1, 1) * gains_.max_rate_roll_pitch, yaw_rate};
    thrust = throttle * max_thrust();
    idle = throttle < gains_.ground_throttle;
  } else if (mode_ == Mode::Manual || mode_ == Mode::Altitude) {
    yaw_setpoint_ = wrap_pi(yaw_setpoint_ + yaw_rate * dt);
    const Quat q_sp =
        stick_attitude(sticks_.roll, sticks_.pitch, yaw_setpoint_, gains_.max_tilt);
    rate_sp = angle_rates(q, q_sp, gains_.angle, {0, 0, yaw_rate});
    if (mode_ == Mode::Manual) {
      thrust = throttle * max_thrust();
      idle = land_.landed() && throttle < gains_.ground_throttle;
    } else if (land_.landed() && altitude_.stick_speed(throttle) >= 0) {
      idle = true;  // on the ground, altitude mode waits for the stick to ask for a climb
      altitude_.reset(height_.z());
    } else {
      thrust = altitude_.update(throttle, height_.z(), height_.vz(), tilt_cos, mass, dt);
    }
  } else {
    Setpoint sp;
    bool done = false;
    if (mode_ == Mode::Position) {
      yaw_setpoint_ = wrap_pi(yaw_setpoint_ + yaw_rate * dt);
      // the sticks in the heading's frame: forward (nose down) and right
      const float forward = -clamp(sticks_.pitch, -1, 1) * auto_.manual_speed;
      const float right = clamp(sticks_.roll, -1, 1) * auto_.manual_speed;
      const float c = std::cos(yaw_setpoint_), s = std::sin(yaw_setpoint_);
      const Vec3 p = position();
      sp.yaw = yaw_setpoint_;
      if (std::fabs(forward) + std::fabs(right) > 0.05f) {
        sp.hold_xy = false;
        sp.v_north = c * forward - s * right;
        sp.v_east = s * forward + c * right;
        hold_.north = p.x;  // letting go holds where it is then
        hold_.east = p.y;
      } else {
        sp.north = hold_.north;
        sp.east = hold_.east;
      }
      const float vz = altitude_.stick_speed(throttle);
      if (vz != 0) {
        sp.hold_z = false;
        sp.vz = vz;
        hold_.z = p.z;
      } else {
        sp.z = hold_.z;
      }
      idle = land_.landed() && vz >= 0;
    } else {
      sp = automatic(dt, done);
      // on the ground only take-off leaves it
      idle = land_.landed() && (mode_ != Mode::Takeoff || phase_ > 0);
    }
    const Thrust t = control_.update(sp, position(), velocity(), mass, dt);
    rate_sp = angle_rates(q, t.attitude, gains_.angle);
    thrust = t.thrust;
    if (done) enter(Mode::Hold);
  }
  if (idle) {
    thrust = 0;
    reset_integrators();
    control_.reset();
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
