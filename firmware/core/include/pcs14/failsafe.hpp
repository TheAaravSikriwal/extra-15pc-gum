// The failsafes: what the drone does by itself when something goes wrong. GPL-3.0.
//
// They follow PX4's, by name and default, so the flight sim's failsafe scenarios mean the same
// thing for both firmwares:
// - lost link: no heartbeat from the ground for COM_DL_LOSS_T, then NAV_DLL_ACT (return)
// - low battery: under BAT_LOW_THR a warning, under BAT_CRIT_THR return, under BAT_EMERGEN_THR
//   land (COM_LOW_BAT_ACT 3, the flight sim's setting)
// - position lost: without a position the automatic modes can't fly, so it comes down on the
//   barometer alone (PX4's "descend")
// - attitude failure: tilted past FD_FAIL_R or FD_FAIL_P for FD_FAIL_R_TTRI, it's out of
//   control; with termination allowed (CBRK_FLIGHTTERM 0, only where there's a chute) the
//   motors stop and the chute goes
// Each failsafe fires once per flight and stays latched, as PX4's do, and each one leaves a
// flag in the log (failsafe_flags), which is how the graders see it.
#pragma once

#include <cstdint>

#include "pcs14/modes.hpp"

namespace pcs14 {

struct FailsafeSettings {
  float link_loss_s = 10.0f;  // COM_DL_LOSS_T
  int link_action = 2;        // NAV_DLL_ACT: 0 off, 1 hold, 2 return, 3 land
  float battery_low = 0.15f;        // BAT_LOW_THR, of the charge
  float battery_critical = 0.07f;   // BAT_CRIT_THR
  float battery_emergency = 0.05f;  // BAT_EMERGEN_THR
  int battery_action = 3;  // COM_LOW_BAT_ACT: 0 warn, 1 return, 2 land, 3 return then land
  float fail_tilt_rad = 60.0f * 3.14159265f / 180;  // FD_FAIL_R and FD_FAIL_P
  float fail_time_s = 0.3f;                         // FD_FAIL_R_TTRI
  bool termination = false;  // CBRK_FLIGHTTERM is 0: flight termination is allowed
};

// what the failsafes see each step
struct FailsafeInputs {
  bool armed = false, in_air = false;
  Mode mode = Mode::Manual;
  bool ground_heard = false;       // a heartbeat from the ground has come in at all
  float ground_silent_s = 0;       // since the last one
  float battery = -1;              // charge left, 0 to 1, or -1 when unknown
  bool position_valid = false;
  bool home_valid = false;
  float tilt_rad = 0;
};

struct FailsafeFlags {
  bool link_lost = false, position_invalid = false, critical_failure = false;
  uint8_t battery_warning = 0;  // 0 none, 1 low, 2 critical, 3 emergency
};

class Failsafes {
 public:
  explicit Failsafes(const FailsafeSettings& s = {}) : s_(s) {}
  void set(const FailsafeSettings& s) { s_ = s; }

  // one step: true with `mode` set when a failsafe wants a mode (Termination included)
  bool update(const FailsafeInputs& in, float dt, Mode& mode);
  const FailsafeFlags& flags() const { return flags_; }
  // clears the latches, as arming does
  void reset();

 private:
  FailsafeSettings s_;
  FailsafeFlags flags_;
  float tilted_s_ = 0;
  bool link_done_ = false, low_done_ = false, critical_done_ = false, emergency_done_ = false,
       position_done_ = false, terminated_ = false;
};

}  // namespace pcs14
