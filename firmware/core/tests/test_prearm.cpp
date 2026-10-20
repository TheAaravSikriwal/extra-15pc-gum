// The pre-arm checks (step 5, task 9): what has to be true before the motors may spin.
#include <doctest/doctest.h>

#include <string>

#include "pcs14/prearm.hpp"

using namespace pcs14;

namespace {
PreArmInputs ready() {
  PreArmInputs in;
  in.imu = in.baro = in.mag = true;
  in.position_valid = true;
  in.mode = Mode::Position;
  in.battery = 0.9f;
  in.monitor_silent_s = 0.01f;
  return in;
}
}  // namespace

TEST_CASE("everything healthy: it may arm") {
  CHECK(prearm_failures(ready()) == 0);
  CHECK(std::string(prearm_reason(0)).empty());
}

TEST_CASE("no live safety monitor, no arming") {
  PreArmInputs in = ready();
  in.monitor_silent_s = 0.6f;  // its heartbeat stopped
  CHECK(prearm_failures(in) == kMonitorQuiet);
  CHECK(std::string(prearm_reason(prearm_failures(in))) == "Preflight Fail: safety monitor quiet");
  in.monitor_silent_s = 0.01f;
  in.monitor_cutting = true;  // alive, but holding the motors off
  CHECK(prearm_failures(in) == kMonitorCutting);
  in.monitor_required = false;  // a bench run with no monitor in the loop
  in.monitor_silent_s = 1e9f;
  in.monitor_cutting = false;
  CHECK(prearm_failures(in) == 0);
}

TEST_CASE("the kill switch on, a sensor missing or no GPS where the mode needs it") {
  PreArmInputs in = ready();
  in.kill_switch = true;
  CHECK((prearm_failures(in) & kKillSwitch) != 0);
  in = ready();
  in.mag = false;
  CHECK(prearm_failures(in) == kNoMag);
  in = ready();
  in.position_valid = false;
  CHECK(prearm_failures(in) == kNoPosition);
  in.mode = Mode::Altitude;  // altitude mode flies without one
  CHECK(prearm_failures(in) == 0);
}

TEST_CASE("the battery blocks arming at critical, as PX4's does; low only warns") {
  PreArmInputs in = ready();
  in.battery = 0.10f;  // under BAT_LOW_THR, over BAT_CRIT_THR
  CHECK(prearm_failures(in) == 0);
  in.battery = 0.06f;  // under BAT_CRIT_THR
  CHECK(prearm_failures(in) == kBatteryCritical);
  in.battery = -1;  // unknown: nothing to judge by
  CHECK(prearm_failures(in) == 0);
}
