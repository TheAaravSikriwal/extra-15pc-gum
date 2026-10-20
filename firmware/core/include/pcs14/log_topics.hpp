// The topics my firmware logs: the ones the flight sim's graders read from PX4's logs
// (pcs14.flight.ulog), under PX4's names and field names, so one reader grades both. GPL-3.0.
#pragma once

#include <array>
#include <cstdint>

#include "pcs14/math.hpp"
#include "pcs14/ulog.hpp"

namespace pcs14 {

// PX4's numbers for the states the graders look at
constexpr uint8_t kArmingStandby = 1, kArmingArmed = 2;  // vehicle_status.arming_state
constexpr uint8_t kNavAcro = 10;                          // vehicle_status.nav_state

// The ground truth: what Gazebo says the drone did, in PX4's north-east-down frame. Only the
// sim has it; on the drone these two stay out of the log.
struct TruthPosition {
  uint64_t t_us;
  Vec3 position, velocity;  // m, m/s
};
struct TruthAttitude {
  uint64_t t_us;
  Quat q;  // body (forward-right-down) to north-east-down
};
// my firmware's own estimate of the same, PX4's vehicle_local_position (from home's take-off
// origin, north-east-down), so the log shows the estimate against the truth
struct EstimateLog {
  uint64_t t_us;
  Vec3 position, velocity;  // m, m/s
};
struct EscSample {
  uint64_t t_us;
  std::array<float, 4> rad_s;  // each motor's commanded speed (PX4's esc_rpm carries rad/s in
                               // the sim, and so does mine)
};
struct ImuLog {
  uint64_t t_us;
  Vec3 gyro, accel;  // rad/s, m/s^2, body frame
};
struct StatusLog {
  uint64_t t_us;
  uint8_t arming_state, nav_state;
};
struct LandLog {
  uint64_t t_us;
  bool landed;
};
struct FailsafeLog {
  uint64_t t_us;
  bool link_lost = false, position_invalid = false, critical_failure = false,
       motor_failure = false;
  uint8_t battery_warning = 0;  // 0 none, 1 low, 2 critical
  bool geofence_breached = false;
};
struct BatteryLog {
  uint64_t t_us;
  float voltage_v, current_a, remaining;  // remaining from 1 (full) to 0
};

// Writes the formats and subscribes to every topic; then each log() writes one sample.
class FlightLogWriter {
 public:
  explicit FlightLogWriter(ULogWriter& out, bool ground_truth);

  void log(const TruthPosition& s);
  void log(const TruthAttitude& s);
  void log(const EstimateLog& s);
  void log(const EscSample& s);
  void log(const ImuLog& s);
  void log(const StatusLog& s);
  void log(const LandLog& s);
  void log(const FailsafeLog& s);
  void log(const BatteryLog& s);

 private:
  ULogWriter& out_;
  bool truth_;
  uint16_t position_ = 0, attitude_ = 0, estimate_, esc_, imu_, status_, land_, failsafe_,
      battery_;
};

}  // namespace pcs14
