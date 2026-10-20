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
