// The pre-arm checks. GPL-3.0.
#include "pcs14/prearm.hpp"

namespace pcs14 {

namespace {
bool needs_position(Mode m) {
  return m == Mode::Position || m == Mode::Takeoff || m == Mode::Hold || m == Mode::Land ||
         m == Mode::Return || m == Mode::Offboard;
}
}  // namespace

uint32_t prearm_failures(const PreArmInputs& in) {
  uint32_t out = 0;
  if (!in.imu) out |= kNoImu;
  if (!in.baro) out |= kNoBaro;
  if (!in.mag) out |= kNoMag;
  if (needs_position(in.mode) && !in.position_valid) out |= kNoPosition;
  if (in.battery >= 0 && in.battery < in.battery_critical) out |= kBatteryCritical;
  if (in.kill_switch) out |= kKillSwitch;
  if (in.monitor_required) {
    if (in.monitor_silent_s > kMonitorTimeoutS) out |= kMonitorQuiet;
    else if (in.monitor_cutting) out |= kMonitorCutting;
  }
  return out;
}

const char* prearm_reason(uint32_t failures) {
  if (failures & kKillSwitch) return "Preflight Fail: kill switch on";
  if (failures & kMonitorQuiet) return "Preflight Fail: safety monitor quiet";
  if (failures & kMonitorCutting) return "Preflight Fail: safety monitor is cutting";
  if (failures & kNoImu) return "Preflight Fail: no IMU";
  if (failures & kNoBaro) return "Preflight Fail: no barometer";
  if (failures & kNoMag) return "Preflight Fail: no compass";
  if (failures & kNoPosition) return "Preflight Fail: no position (GPS)";
  if (failures & kBatteryCritical) return "Preflight Fail: battery critical";
  return "";
}

}  // namespace pcs14
