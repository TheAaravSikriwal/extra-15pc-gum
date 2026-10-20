// The safety monitor's core: the Teensy 4.1 in Base, with its own IMU, watching the flight
// controller and ready to cut the motors. GPL-3.0.
//
// It cuts by taking over the ESC signal lines and sending DShot stop frames, never by
// switching the main power, so if it loses power the drone keeps flying. It cuts:
// - on the kill switch, always (the switch reaches the motors through both boards)
// - when the flight controller's heartbeat stops (a hung flight controller)
// - on its automatic triggers (free fall, tumbling), but only once they're out of shadow mode;
//   in shadow mode they're logged and nothing else, until they've shown zero false triggers
// A cut stays latched for the rest of the flight: it clears only on the ground, with the
// flight controller disarmed and the kill switch off. (Proposed 2026-10-20 as the answer to
// "can a cut be undone in the air"; it's a safety rule, so it's Aarav's to confirm.)
#pragma once

#include <cstdint>
#include <vector>

#include "pcs14/attitude.hpp"
#include "pcs14/math.hpp"

namespace pcs14 {

// the automatic triggers' thresholds, as design/targets.yaml has them. Doubles, so "held for
// 0.3 s" means the same sample as in the Python reference (0.3f is a hair over 0.3)
struct TriggerLimits {
  double free_fall_g = 0.3, free_fall_s = 0.3;
  double tumble_rate_dps = 400.0, tumble_rate_s = 0.3;
  double tumble_tilt_deg = 75.0, tumble_tilt_s = 0.5;
};

enum class TriggerKind : uint8_t { FreeFall, TumbleRate, TumbleTilt };
const char* trigger_name(TriggerKind kind);

struct Trigger {
  TriggerKind kind;
  double at, since;  // s: when it fired, and when its condition started
};

// The triggers, exactly as pcs14.safety.triggers has them: each fires once, at the moment its
// condition has held long enough, and re-arms when the condition clears.
class TriggerWatch {
 public:
  explicit TriggerWatch(const TriggerLimits& limits = {}) : limits_(limits) {}
  // one IMU sample: accel (m/s^2, what the IMU feels), gyro (rad/s), tilt (rad from level);
  // returns how many triggers fired on it, appended to `fired`
  int update(double t, const Vec3& accel, const Vec3& gyro, float tilt,
             std::vector<Trigger>& fired);

 private:
  TriggerLimits limits_;
  double started_[3]{};
  bool holding_[3]{}, fired_[3]{};
};

enum class Cut : uint8_t { None, KillSwitch, FlightControllerSilent, Trigger };
const char* cut_name(Cut cut);

struct MonitorSettings {
  TriggerLimits limits;
  float heartbeat_timeout_s = 0.25f;  // the flight controller silent this long: it's hung
  bool shadow = true;                 // the automatic triggers only log
};

class Monitor {
 public:
  explicit Monitor(const MonitorSettings& settings = {});

  // one step on its own IMU, at `t` s: `heartbeat` when a heartbeat from the flight controller
  // came in since the last step, `armed` as that heartbeat says, `kill` the kill switch
  void update(double t, const Vec3& gyro, const Vec3& accel, bool heartbeat, bool armed,
              bool kill, float dt);

  bool cutting() const { return cut_ != Cut::None; }
  Cut why() const { return cut_; }
  double cut_at() const { return cut_at_; }
  // every trigger that has fired, shadow or not: the log the false-trigger count comes from
  const std::vector<Trigger>& triggers() const { return triggers_; }
  const Attitude& attitude() const { return attitude_; }

 private:
  void cut(Cut why, double t);
  MonitorSettings s_;
  Attitude attitude_;
  TriggerWatch watch_;
  std::vector<Trigger> triggers_;
  Cut cut_ = Cut::None;
  double cut_at_ = 0, last_heartbeat_ = -1;
  bool fc_armed_ = false;
};

// A DShot frame: an 11-bit value (0 is "stop", 48 to 2047 throttle), the telemetry bit, and a
// 4-bit checksum, 16 bits in all. The safety monitor sends stop frames after a takeover, and
// the flight controller fresh frames every loop, so a hung processor means the motors stop.
uint16_t dshot_frame(uint16_t value, bool telemetry = false);
constexpr uint16_t kDshotStop = 0;

}  // namespace pcs14
