// The safety monitor's core: what cuts, what only logs, and what clears a cut.
#include <doctest/doctest.h>

#include <vector>

#include "pcs14/monitor.hpp"

using namespace pcs14;

namespace {
constexpr float kDt = 0.004f;
const Vec3 kStill{0, 0, -kG};  // a level, still IMU, forward-right-down

// flies the monitor for `seconds`: the flight controller's heartbeat every 0.1 s while
// `beating`, the IMU as given
void run(Monitor& m, double& t, double seconds, bool beating, bool armed, bool kill,
         const Vec3& gyro = {}, const Vec3& accel = kStill) {
  static long step = 0;
  const long steps = static_cast<long>(seconds / kDt + 0.5);
  for (long k = 0; k < steps; ++k, ++step, t += kDt) {
    const bool beat = beating && step % 25 == 0;
    m.update(t, gyro, accel, beat, armed, kill, kDt);
  }
}
}  // namespace

TEST_CASE("the kill switch cuts at once, always") {
  Monitor m;
  double t = 0;
  run(m, t, 1.0, true, true, false);
  CHECK_FALSE(m.cutting());
  run(m, t, 0.01, true, true, true);
  CHECK(m.cutting());
  CHECK(m.why() == Cut::KillSwitch);
}

TEST_CASE("a silent flight controller is cut, but only when it was armed") {
  Monitor m;
  double t = 0;
  run(m, t, 1.0, true, false, false);
  run(m, t, 1.0, false, false, false);  // disarmed and quiet: nothing to stop
  CHECK_FALSE(m.cutting());
  run(m, t, 1.0, true, true, false);
  run(m, t, 0.2, false, true, false);
  CHECK_FALSE(m.cutting());  // under the 0.25 s timeout
  run(m, t, 0.2, false, true, false);
  CHECK(m.cutting());
  CHECK(m.why() == Cut::FlightControllerSilent);
}

TEST_CASE("in shadow mode a tumble is logged and nothing else") {
  Monitor m;  // shadow by default
  double t = 0;
  run(m, t, 1.0, true, true, false);
  run(m, t, 0.5, true, true, false, {8.0f, 0, 0});  // 460 degrees a second
  CHECK_FALSE(m.cutting());
  REQUIRE_FALSE(m.triggers().empty());
  CHECK(m.triggers()[0].kind == TriggerKind::TumbleRate);
}

TEST_CASE("out of shadow mode a free fall cuts") {
  MonitorSettings s;
  s.shadow = false;
  Monitor m(s);
  double t = 0;
  run(m, t, 1.0, true, true, false);
  run(m, t, 0.5, true, true, false, {}, {0, 0, -0.5f});  // falling: nearly nothing felt
  CHECK(m.cutting());
  CHECK(m.why() == Cut::Trigger);
}

TEST_CASE("a cut stays latched in the air and clears on the ground, disarmed, switch off") {
  Monitor m;
  double t = 0;
  run(m, t, 1.0, true, true, false);
  run(m, t, 0.1, true, true, true);
  REQUIRE(m.cutting());
  run(m, t, 1.0, true, true, false);  // switch off, but the flight controller is still armed
  CHECK(m.cutting());
  run(m, t, 1.0, true, false, false);  // disarmed, on the ground
  CHECK_FALSE(m.cutting());
}

TEST_CASE("DShot frames: the value, the telemetry bit and the checksum") {
  // 1046 with telemetry off, a commonly worked example: 0x82c6
  CHECK(dshot_frame(1046) == 0x82c6);
  CHECK(dshot_frame(kDshotStop) == 0x0000);
  // the checksum is the xor of the three nibbles above it
  const uint16_t f = dshot_frame(48, true);
  CHECK(((f >> 4) ^ (f >> 8) ^ (f >> 12) ^ f) % 16 == 0);
}
