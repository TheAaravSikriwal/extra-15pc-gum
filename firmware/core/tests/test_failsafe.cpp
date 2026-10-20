// The failsafes (step 5, task 9): each fires once, in PX4's order, and flies what it asks for.
#include <doctest/doctest.h>

#include "pcs14/failsafe.hpp"
#include "pcs14/flight.hpp"
#include "plant.hpp"

using namespace pcs14;

namespace {
FailsafeInputs flying() {
  FailsafeInputs in;
  in.armed = in.in_air = true;
  in.mode = Mode::Offboard;
  in.ground_heard = true;
  in.position_valid = in.home_valid = true;
  return in;
}
}  // namespace

TEST_CASE("a lost link returns after the timeout, once") {
  Failsafes f;
  FailsafeInputs in = flying();
  Mode m{};
  in.ground_silent_s = 9.0f;
  CHECK_FALSE(f.update(in, 0.1f, m));
  CHECK_FALSE(f.flags().link_lost);
  in.ground_silent_s = 10.5f;
  REQUIRE(f.update(in, 0.1f, m));
  CHECK(m == Mode::Return);
  CHECK(f.flags().link_lost);
  in.mode = Mode::Return;
  CHECK_FALSE(f.update(in, 0.1f, m));  // latched: it doesn't keep asking
}

TEST_CASE("a battery running down warns, returns, then lands") {
  FailsafeSettings s;
  s.battery_low = 0.35f;
  s.battery_critical = 0.30f;
  Failsafes f(s);
  FailsafeInputs in = flying();
  Mode m{};
  in.battery = 0.34f;
  CHECK_FALSE(f.update(in, 0.1f, m));
  CHECK(f.flags().battery_warning == 1);
  in.battery = 0.29f;
  REQUIRE(f.update(in, 0.1f, m));
  CHECK(m == Mode::Return);
  in.battery = 0.04f;
  REQUIRE(f.update(in, 0.1f, m));
  CHECK(m == Mode::Land);
}

TEST_CASE("tilted past the limit long enough, it terminates where that's allowed") {
  FailsafeSettings s;
  s.termination = true;
  Failsafes f(s);
  FailsafeInputs in = flying();
  Mode m{};
  in.tilt_rad = 1.2f;  // 69 degrees
  CHECK_FALSE(f.update(in, 0.2f, m));  // not long enough yet
  REQUIRE(f.update(in, 0.2f, m));
  CHECK(m == Mode::Termination);
  CHECK(f.flags().critical_failure);

  Failsafes without;  // no chute, no termination: the flag, and nothing else to do
  Mode n{};
  CHECK_FALSE(without.update(in, 0.2f, n));
  CHECK_FALSE(without.update(in, 0.2f, n));
  CHECK(without.flags().critical_failure);
}

TEST_CASE("losing the position in an automatic mode brings it down") {
  Failsafes f;
  FailsafeInputs in = flying();
  in.position_valid = false;
  Mode m{};
  REQUIRE(f.update(in, 0.1f, m));
  CHECK(m == Mode::Land);
  CHECK(f.flags().position_invalid);
}

TEST_CASE("terminated, the motors stop for good") {
  Flight flight(test::base_airframe());
  test::Plant plant(test::base_airframe());
  flight.arm();
  flight.set_sticks({0, 0, 0, 0.5f});
  Mix m = flight.step(plant.rate, plant.accel(), 0.004f);
  CHECK(m.rad_s[0] > 0.0f);
  REQUIRE(flight.set_mode(Mode::Termination));
  m = flight.step(plant.rate, plant.accel(), 0.004f);
  for (float w : m.rad_s) CHECK(w == 0.0f);
  CHECK_FALSE(flight.set_mode(Mode::Acro));  // no way back
}

TEST_CASE("a failed motor gets nothing, and the mixer knows it's short") {
  Flight flight(test::base_airframe());
  test::Plant plant(test::base_airframe());
  flight.arm();
  flight.set_sticks({0, 0, 0, 0.5f});
  flight.fail_motor(1);
  const Mix m = flight.step(plant.rate, plant.accel(), 0.004f);
  CHECK(m.rad_s[1] == 0.0f);
  CHECK(m.rad_s[0] > 0.0f);
  CHECK(m.saturated);
}

TEST_CASE("past the geofence it holds, once a breach, and asks again after coming back in") {
  FailsafeSettings s;
  s.fence_m = 50;  // GF_MAX_HOR_DIST, with PX4's default GF_ACTION 2: hold
  Failsafes f(s);
  FailsafeInputs in = flying();
  Mode m{};
  in.distance_m = 49;
  CHECK_FALSE(f.update(in, 0.1f, m));
  in.distance_m = 51;
  REQUIRE(f.update(in, 0.1f, m));
  CHECK(m == Mode::Hold);
  CHECK(f.flags().geofence_breached);
  in.mode = Mode::Hold;
  CHECK_FALSE(f.update(in, 0.1f, m));  // one breach, one ask
  in.distance_m = 40;                  // flown back in by hand
  CHECK_FALSE(f.update(in, 0.1f, m));
  CHECK_FALSE(f.flags().geofence_breached);
  in.distance_m = 52;
  REQUIRE(f.update(in, 0.1f, m));
  CHECK(m == Mode::Hold);
}

TEST_CASE("over the fence's height it does what GF_ACTION says, and no fence is no fence") {
  FailsafeSettings s;
  s.fence_height_m = 100;  // GF_MAX_VER_DIST
  s.fence_action = 3;      // return
  Failsafes f(s);
  FailsafeInputs in = flying();
  Mode m{};
  in.height_m = 101;
  REQUIRE(f.update(in, 0.1f, m));
  CHECK(m == Mode::Return);

  Failsafes none;  // both 0, PX4's defaults
  in.distance_m = 5000;
  in.height_m = 900;
  CHECK_FALSE(none.update(in, 0.1f, m));
  CHECK_FALSE(none.flags().geofence_breached);

  s.fence_action = 4;  // terminate, but termination isn't allowed without the chute: land
  Failsafes no_chute(s);
  in.height_m = 101;
  REQUIRE(no_chute.update(in, 0.1f, m));
  CHECK(m == Mode::Land);
}
