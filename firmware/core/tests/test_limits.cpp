// The current cap's heat limit against the electrical report's numbers, and the limits.
#include <doctest/doctest.h>

#include <string>

#include "pcs14/limits.hpp"

using namespace pcs14;
using doctest::Approx;

TEST_CASE("the XT60's heat model is the electrical report's") {
  const ConnectorHeat h;
  CHECK(h.holds() == Approx(29.4f).epsilon(0.01));  // "29 A, which it holds forever"
  CHECK(h.time_constant() == Approx(97.6f).epsilon(0.02));
  CHECK(h.rise_per_amp2() * 25.12f * 25.12f == Approx(44.0f).epsilon(0.01));  // Max's hover
}

TEST_CASE("from Max's hover, 90 A lasts about 3.1 s, then the cap eases toward 29 A") {
  const ConnectorHeat h;
  CurrentCap cap(90.0f, h, h.rise_per_amp2() * 25.12f * 25.12f);
  const float dt = 0.01f;
  float t = 0, first_eased = -1;
  for (; t < 60; t += dt) {
    const float allowed = cap.allowed(dt);
    if (allowed < 89.9f && first_eased < 0) first_eased = t;
    cap.update(allowed, dt);  // the motors take all they're allowed: the worst case
  }
  CHECK(first_eased == Approx(3.1f).epsilon(0.05));
  CHECK(cap.temperature() <= 100.0f + 1e-3f);
  CHECK(cap.allowed(dt) == Approx(29.4f).epsilon(0.02));
}

TEST_CASE("a cool connector gets the full cap, and cools back down") {
  CurrentCap cap;
  CHECK(cap.allowed(0.01f) == Approx(90.0f));
  for (int k = 0; k < 2000; ++k) cap.update(60.0f, 0.01f);
  const float warm = cap.rise();
  for (int k = 0; k < 2000; ++k) cap.update(0.0f, 0.01f);
  CHECK(cap.rise() < warm);
}

TEST_CASE("the profiles' ceilings, and the parachute rule without the chute") {
  CHECK(std::string(limits_profile(1).name) == "us-recreational");
  CHECK(allowed_height(limits_profile(1), true) == Approx(121.92f));
  CHECK(allowed_height(limits_profile(1), false) == Approx(30.0f));
  CHECK(allowed_height(limits_profile(0), true) > 1000.0f);  // max: none
  CHECK(allowed_height(limits_profile(0), false) == Approx(30.0f));
}
