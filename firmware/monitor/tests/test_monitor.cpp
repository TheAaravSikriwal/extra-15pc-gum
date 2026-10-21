// The safety monitor's core: what cuts, what only logs, and what clears a cut.
#include <doctest/doctest.h>

#include <vector>

#include "pcs14/monitor.hpp"

using namespace pcs14;

namespace {
constexpr float kDt = 0.004f;
const Vec3 kStill{0, 0, -kG};  // a level, still IMU, forward-right-down

// a monitor on a drone with P fitted
MonitorSettings with_chute() {
  MonitorSettings s;
  s.chute_fitted = true;
  return s;
}

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

TEST_CASE("the pilot's chute switch cuts the motors first, then lets the chute go") {
  Monitor m(with_chute());
  double t = 0;
  run(m, t, 1.0, true, true, false);
  m.fire_chute(t);
  CHECK(m.cutting());
  CHECK(m.why() == Cut::Chute);
  CHECK(m.releasing());
  CHECK(m.release_at() >= m.cut_at());  // never the canopy before the stop frames
}

TEST_CASE("on the ground, disarmed, the chute switch does nothing") {
  Monitor m(with_chute());
  double t = 0;
  run(m, t, 1.0, true, false, false);
  m.fire_chute(t);
  CHECK_FALSE(m.releasing());
  CHECK_FALSE(m.cutting());
}

TEST_CASE("with the flight controller hung, the pilot's chute still goes") {
  Monitor m(with_chute());
  double t = 0;
  run(m, t, 1.0, true, true, false);
  run(m, t, 0.5, false, true, false);  // hung: the monitor has cut already
  REQUIRE(m.why() == Cut::FlightControllerSilent);
  m.fire_chute(t);
  CHECK(m.releasing());
  CHECK(m.why() == Cut::FlightControllerSilent);  // the first reason stays the reason
}

TEST_CASE("without P the chute switch does nothing: no chute to fire, so no cut either") {
  Monitor m;
  double t = 0;
  run(m, t, 1.0, true, true, false);
  m.fire_chute(t);
  CHECK_FALSE(m.cutting());
  CHECK_FALSE(m.releasing());
}

TEST_CASE("out of shadow mode a free fall fires the chute too, where there is one") {
  for (const bool fitted : {true, false}) {
    MonitorSettings s;
    s.shadow = false;
    s.chute_fitted = fitted;
    Monitor m(s);
    double t = 0;
    run(m, t, 1.0, true, true, false);
    run(m, t, 0.5, true, true, false, {}, {0, 0, -0.5f});
    CHECK(m.cutting());
    CHECK(m.releasing() == fitted);
  }
}

TEST_CASE("in shadow mode a free fall fires nothing, chute or not") {
  MonitorSettings s;
  s.chute_fitted = true;
  Monitor m(s);
  double t = 0;
  run(m, t, 1.0, true, true, false);
  run(m, t, 0.5, true, true, false, {}, {0, 0, -0.5f});
  CHECK_FALSE(m.releasing());
  CHECK_FALSE(m.cutting());
}

TEST_CASE("the release stays latched in the air and clears with the cut, on the ground") {
  Monitor m(with_chute());
  double t = 0;
  run(m, t, 1.0, true, true, false);
  m.fire_chute(t);
  run(m, t, 1.0, true, true, false);
  CHECK(m.releasing());
  run(m, t, 1.0, true, false, false);  // down, and disarmed
  CHECK_FALSE(m.releasing());
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
