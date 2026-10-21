// The safety monitor's core. GPL-3.0.
#include "pcs14/monitor.hpp"

#include <cmath>

namespace pcs14 {

const char* trigger_name(TriggerKind kind) {
  switch (kind) {
    case TriggerKind::FreeFall:
      return "free fall";
    case TriggerKind::TumbleRate:
      return "tumble rate";
    default:
      return "tumble tilt";
  }
}

const char* cut_name(Cut cut) {
  switch (cut) {
    case Cut::KillSwitch:
      return "kill switch";
    case Cut::FlightControllerSilent:
      return "flight controller silent";
    case Cut::Trigger:
      return "trigger";
    case Cut::Chute:
      return "chute";
    default:
      return "none";
  }
}

int TriggerWatch::update(double t, const Vec3& accel, const Vec3& gyro, float tilt,
                         std::vector<Trigger>& fired) {
  const double deg = 3.14159265358979323846 / 180;
  const bool holds[3] = {accel.norm() < limits_.free_fall_g * 9.80665,
                         gyro.norm() > limits_.tumble_rate_dps * deg,
                         tilt > limits_.tumble_tilt_deg * deg};
  const double hold_s[3] = {limits_.free_fall_s, limits_.tumble_rate_s, limits_.tumble_tilt_s};
  int count = 0;
  for (int k = 0; k < 3; ++k) {
    if (!holds[k]) {
      holding_[k] = fired_[k] = false;
      continue;
    }
    if (!holding_[k]) {
      holding_[k] = true;
      started_[k] = t;
    }
    if (!fired_[k] && t - started_[k] >= hold_s[k] - 1e-9) {
      fired.push_back({static_cast<TriggerKind>(k), t, started_[k]});
      fired_[k] = true;
      ++count;
    }
  }
  return count;
}

Monitor::Monitor(const MonitorSettings& settings) : s_(settings), watch_(settings.limits) {}

void Monitor::cut(Cut why, double t) {
  if (cut_ != Cut::None) return;
  cut_ = why;
  cut_at_ = t;
}

void Monitor::update(double t, const Vec3& gyro, const Vec3& accel, bool heartbeat, bool armed,
                     bool kill, float dt) {
  attitude_.update(gyro, accel, nullptr, dt);
  if (heartbeat) {
    last_heartbeat_ = t;
    fc_armed_ = armed;
  }
  // the latch clears only on the ground: disarmed, and the switch off
  if (cut_ != Cut::None && !kill && heartbeat && !armed) {
    cut_ = Cut::None;
    releasing_ = false;
  }
  if (kill) cut(Cut::KillSwitch, t);
  if (fc_armed_ && last_heartbeat_ >= 0 && t - last_heartbeat_ > s_.heartbeat_timeout_s)
    cut(Cut::FlightControllerSilent, t);
  // the IMU feels the specific force; the reference takes "about (0, 0, g) hovering", so the
  // sign doesn't matter for the free-fall test, only the size
  const int fired = watch_.update(t, accel, gyro, attitude_.q().tilt(), triggers_);
  if (fired > 0 && !s_.shadow && fc_armed_) {
    cut(Cut::Trigger, t);
    if (s_.chute_fitted) release(t);
  }
}

void Monitor::fire_chute(double t) {
  // without P there's no chute, and cutting the motors for one would drop the drone; on the
  // ground there's nothing to save
  if (!s_.chute_fitted || !fc_armed_) return;
  cut(Cut::Chute, t);
  release(t);
}

// the release only ever follows a cut: the stop frames are going out before the chute does
void Monitor::release(double t) {
  if (cut_ == Cut::None || releasing_) return;
  releasing_ = true;
  release_at_ = t;
}

uint16_t dshot_frame(uint16_t value, bool telemetry) {
  const uint16_t v = static_cast<uint16_t>(((value & 0x7ff) << 1) | (telemetry ? 1 : 0));
  const uint16_t crc = (v ^ (v >> 4) ^ (v >> 8)) & 0xf;
  return static_cast<uint16_t>((v << 4) | crc);
}

}  // namespace pcs14
