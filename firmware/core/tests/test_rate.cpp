// The rate controller on a modeled axis: an inertia the controller's torque turns, plus a
// disturbance, worked step by step.
#include <doctest/doctest.h>

#include <algorithm>

#include "pcs14/rate.hpp"

using namespace pcs14;
using doctest::Approx;

namespace {
constexpr float kDt = 1.0f / 1000;  // the rate loop runs at 1 kHz

// one axis: the controller asks for an angular acceleration, the airframe answers with it
// (plus whatever the disturbance adds), and a motor lag delays it a little
struct Axis {
  float rate = 0, lagged = 0, tau_motor = 0.02f;
  void step(float wanted_accel, float disturbance, float dt) {
    lagged += (wanted_accel - lagged) * dt / tau_motor;
    rate += (lagged + disturbance) * dt;
  }
};
}  // namespace

// gains in the range a rate loop on this size of drone runs (a Python run of the same loop,
// 2026-10-20: 10% overshoot, inside 0.3% after 2 s, a steady push taken out completely)
const RateGains kGains{20.0f, 40.0f, 0.5f, 0.0f, 40.0f, 400.0f, 50.0f};

TEST_CASE("a rate step settles with little overshoot") {
  RateAxis pid(kGains);
  Axis axis;
  float peak = 0;
  for (int k = 0; k < 2000; ++k) {
    const float out = pid.update(1.0f, axis.rate, kDt, false);
    axis.step(out, 0, kDt);
    peak = std::max(peak, axis.rate);
  }
  CHECK(axis.rate == Approx(1.0f).epsilon(0.005));
  CHECK(peak < 1.15f);
}

TEST_CASE("the integrator takes out a steady disturbance") {
  RateAxis pid(kGains);
  Axis axis;
  for (int k = 0; k < 5000; ++k) {
    const float out = pid.update(0.0f, axis.rate, kDt, false);
    axis.step(out, 3.0f, kDt);  // a constant 3 rad/s^2 push, like an off-center weight
  }
  CHECK(std::abs(axis.rate) < 0.005f);
}

TEST_CASE("the output is limited and the integrator doesn't wind up while saturated") {
  RateAxis pid({8.0f, 4.0f, 0.05f, 0.0f, 10.0f, 50.0f, 50.0f});
  for (int k = 0; k < 2000; ++k) {
    const float out = pid.update(10.0f, 0.0f, kDt, true);  // the mixer says it's saturated
    CHECK(std::abs(out) <= 50.0f + 1e-4f);
  }
  CHECK(std::abs(pid.integral()) < 1e-6f);  // frozen while the motors had nothing left
}

TEST_CASE("the derivative works on the measurement, so a setpoint step doesn't kick it") {
  RateAxis pid({0.0f, 0.0f, 1.0f, 0.0f, 40.0f, 1000.0f, 1000.0f});
  pid.update(0.0f, 0.0f, kDt, false);
  CHECK(pid.update(5.0f, 0.0f, kDt, false) == Approx(0.0f));  // the setpoint jumped, nothing moved
}

TEST_CASE("feed-forward passes the setpoint straight through") {
  RateAxis pid({0.0f, 0.0f, 0.0f, 2.0f, 40.0f, 1000.0f, 1000.0f});
  CHECK(pid.update(3.0f, 3.0f, kDt, false) == Approx(6.0f));
}
