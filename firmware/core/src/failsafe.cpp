// The failsafes. GPL-3.0.
#include "pcs14/failsafe.hpp"

namespace pcs14 {

namespace {
bool automatic(Mode m) {
  return m == Mode::Position || m == Mode::Takeoff || m == Mode::Hold || m == Mode::Land ||
         m == Mode::Return || m == Mode::Offboard;
}
}  // namespace

void Failsafes::reset() {
  flags_ = {};
  tilted_s_ = 0;
  link_done_ = low_done_ = critical_done_ = emergency_done_ = position_done_ = fence_done_ = false;
  terminated_ = false;
}

bool Failsafes::update(const FailsafeInputs& in, float dt, Mode& mode) {
  // the flags follow the facts whether or not anything is done about them
  flags_.link_lost = in.ground_heard && in.ground_silent_s > s_.link_loss_s;
  flags_.position_invalid = !in.position_valid;
  if (in.battery >= 0) {
    flags_.battery_warning = in.battery < s_.battery_emergency  ? 3
                             : in.battery < s_.battery_critical ? 2
                             : in.battery < s_.battery_low      ? 1
                                                                : 0;
  }
  const bool outside = in.home_valid && in.position_valid &&
                       ((s_.fence_m > 0 && in.distance_m > s_.fence_m) ||
                        (s_.fence_height_m > 0 && in.height_m > s_.fence_height_m));
  flags_.geofence_breached = outside;
  if (!outside) fence_done_ = false;  // back inside: the next breach asks again
  if (!in.armed || !in.in_air) {
    tilted_s_ = 0;
    return false;
  }
  // out of control: tilted past the limit for long enough
  tilted_s_ = in.tilt_rad > s_.fail_tilt_rad ? tilted_s_ + dt : 0;
  if (tilted_s_ >= s_.fail_time_s) flags_.critical_failure = true;
  if (flags_.critical_failure && s_.termination && !terminated_) {
    terminated_ = true;
    mode = Mode::Termination;
    return true;
  }
  if (terminated_) return false;
  // no position in an automatic mode: come down (Land without a position holds no spot)
  if (flags_.position_invalid && automatic(in.mode) && !position_done_) {
    position_done_ = true;
    mode = Mode::Land;
    return true;
  }
  if (flags_.position_invalid) return false;  // the rest need a position
  // low battery, by COM_LOW_BAT_ACT
  if (flags_.battery_warning >= 3 && !emergency_done_ && s_.battery_action >= 2) {
    emergency_done_ = true;
    mode = Mode::Land;
    return true;
  }
  if (flags_.battery_warning >= 2 && !critical_done_ && s_.battery_action >= 1) {
    critical_done_ = true;
    mode = s_.battery_action == 2 || !in.home_valid ? Mode::Land : Mode::Return;
    return true;
  }
  if (flags_.battery_warning >= 1) low_done_ = true;  // a warning only
  // the geofence, by GF_ACTION
  if (outside && !fence_done_) {
    fence_done_ = true;
    switch (s_.fence_action) {
      case 2: mode = Mode::Hold; return true;
      case 3: mode = in.home_valid ? Mode::Return : Mode::Land; return true;
      case 4: mode = s_.termination ? Mode::Termination : Mode::Land; return true;
      case 5: mode = Mode::Land; return true;
      default: break;  // none, or a warning: the flag only
    }
  }
  // lost link, by NAV_DLL_ACT
  if (flags_.link_lost && !link_done_ && s_.link_action != 0) {
    link_done_ = true;
    if (s_.link_action == 1) mode = Mode::Hold;
    else if (s_.link_action == 2 && in.home_valid) mode = Mode::Return;
    else mode = Mode::Land;
    return true;
  }
  return false;
}

}  // namespace pcs14
