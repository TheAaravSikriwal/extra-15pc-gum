// The pre-arm checks: what has to be true before the motors may spin. GPL-3.0.
//
// PX4's idea (its HealthAndArmingChecks), with the checks this drone needs: the sensors are
// alive, the GPS has a position when the mode needs one, the battery isn't critical, the kill
// switch is off, and the safety monitor is alive and not cutting (docs/decisions.md, "Safety
// basics": the flight controller won't arm without a live monitor). The battery rule is PX4's:
// under BAT_CRIT_THR it won't arm, under BAT_LOW_THR it only warns. Each failure has a reason,
// sent to the ground the way PX4 sends its "Preflight Fail" messages.
#pragma once

#include <cstdint>

#include "pcs14/modes.hpp"

namespace pcs14 {

constexpr float kMonitorTimeoutS = 0.5f;  // s without the monitor's heartbeat: it's quiet

struct PreArmInputs {
  bool imu = false, baro = false, mag = false;  // each one's samples coming in
  bool position_valid = false;                  // the GPS and the position filter
  Mode mode = Mode::Manual;                     // the mode it would arm into
  float battery = -1;                           // charge left, 0 to 1, or -1 when unknown
  float battery_critical = 0.07f;               // BAT_CRIT_THR
  bool kill_switch = false;                     // on means stop
  bool monitor_required = true;                 // false only with no monitor in the loop
  float monitor_silent_s = 1e9f;                // since its last heartbeat
  bool monitor_cutting = false;
};

enum PreArmFailure : uint32_t {
  kNoImu = 1u << 0,
  kNoBaro = 1u << 1,
  kNoMag = 1u << 2,
  kNoPosition = 1u << 3,
  kBatteryCritical = 1u << 4,
  kKillSwitch = 1u << 5,
  kMonitorQuiet = 1u << 6,
  kMonitorCutting = 1u << 7,
};

// every failing check, as PreArmFailure bits; 0 means it may arm
uint32_t prearm_failures(const PreArmInputs& in);
// the first failing check in words ("Preflight Fail: ..."), or "" when none fail
const char* prearm_reason(uint32_t failures);

}  // namespace pcs14
