// Self-level and altitude hold (step 5, task 7), on the host's rigid-body quad.
#include <doctest/doctest.h>

#include <algorithm>
#include <cmath>
#include <random>
#include <string>
#include <vector>

#include "pcs14/flight.hpp"
#include "pcs14/height.hpp"
#include "pcs14/land.hpp"
#include "plant.hpp"

using namespace pcs14;
using doctest::Approx;

namespace {
constexpr float kDt = 1.0f / 250;
constexpr int kBaroEvery = 5;  // 50 Hz, like the sim's barometer
constexpr int kGpsEvery = 25;  // 10 Hz, a GPS's velocity

struct Sim {
  Flight flight;
  test::Plant plant;
  std::mt19937 rng{7};
  std::normal_distribution<float> baro_noise{0.0f, 3.0f};  // Pa, the sim's barometer noise
  int k = 0;

  Sim() : flight(test::base_airframe()), plant(test::base_airframe()) {}

  // flies `seconds`; returns the largest tilt in degrees and fills the height range seen
  float fly(float seconds, float* low = nullptr, float* high = nullptr) {
    float worst = 0;
    for (int n = 0; n < static_cast<int>(seconds / kDt); ++n, ++k) {
      if (k % kBaroEvery == 0)
        flight.on_baro(plant.pressure() + baro_noise(rng), kDt * kBaroEvery);
      if (k % kGpsEvery == 0) flight.on_gps_velocity(plant.velocity, kDt * kGpsEvery);
      const Mix m = flight.step(plant.rate, plant.accel(), kDt);
      plant.step(m.rad_s, kDt);
      worst = std::max(worst, plant.q.tilt() * 180 / kPi);
      const float h = -plant.position.z;
      if (low) *low = std::min(*low, h);
      if (high) *high = std::max(*high, h);
    }
    return worst;
  }
};
}  // namespace

TEST_CASE("the barometer's height from the standard atmosphere") {
  CHECK(pressure_height(101325.0f, 101325.0f) == Approx(0.0f));
  // about 12 Pa a meter near the ground
  CHECK(pressure_height(101325.0f - 120.0f, 101325.0f) == Approx(10.0f).epsilon(0.02));
}

TEST_CASE("the height filter follows a climb and learns the accelerometer's bias") {
  HeightFilter f(1.0f);
  float z = 0, vz = 0;
  const float bias = 0.3f;  // m/s^2 the accelerometer reads too high
  for (int k = 0; k < 250 * 60; ++k) {
    const float t = static_cast<float>(k) * kDt;
    const float a = t > 20 && t < 22 ? -1.0f : (t > 22 && t < 24 ? 1.0f : 0.0f);  // up 2 m/s
    vz += a * kDt;
    z += vz * kDt;
    f.predict(a - kG + bias, kDt);  // what the accelerometer feels, with its bias
    if (k % kBaroEvery == 0) f.correct(z, kDt * kBaroEvery);
  }
  CHECK(f.bias() == Approx(bias).epsilon(0.05));
  CHECK(f.z() == Approx(z).epsilon(0.01));
  CHECK(f.vz() == Approx(vz).epsilon(0.05));
}

TEST_CASE("self-level: a roll stick leans the drone, and letting go levels it") {
  Sim s;
  s.flight.set_mode(Mode::Manual);
  s.flight.arm();
  s.flight.set_sticks({0, 0, 0, s.flight.hover_throttle() * 1.15f});
  s.fly(2.0f);
  s.flight.set_sticks({0.5f, 0, 0, s.flight.hover_throttle()});
  s.fly(2.0f);
  CHECK(s.plant.q.roll() * 180 / kPi == Approx(17.5f).epsilon(0.05));  // half of 35 degrees
  s.flight.set_sticks({0, 0, 0, s.flight.hover_throttle()});
  s.fly(2.0f);
  // braking from the sideways run: the GPS's acceleration lags a little (10 Hz, smoothed)
  CHECK(std::abs(s.plant.q.roll()) * 180 / kPi < 2.0f);
  s.fly(4.0f);
  CHECK(std::abs(s.plant.q.roll()) * 180 / kPi < 0.5f);
}

TEST_CASE("altitude mode climbs on the stick, and holds the height when it's centered") {
  Sim s;
  REQUIRE(s.flight.set_mode(Mode::Altitude));
  s.flight.arm();
  s.flight.set_sticks({0, 0, 0, 0.5f});  // centered on the ground: it waits
  s.fly(2.0f);
  CHECK(s.plant.on_ground());
  s.flight.set_sticks({0, 0, 0, 0.8f});
  s.fly(4.0f);
  const float climbed = -s.plant.position.z;
  CHECK(climbed > 3.0f);
  s.flight.set_sticks({0, 0, 0, 0.5f});
  s.fly(3.0f);  // braking
  const float held = -s.plant.position.z;
  float low = held, high = held;
  s.fly(10.0f, &low, &high);
  CHECK(high - low < 0.6f);  // with 3 Pa of barometer noise, about 25 cm
  CHECK(s.flight.armed());
}

TEST_CASE("altitude mode comes down on the stick, lands and disarms itself") {
  Sim s;
  s.flight.set_mode(Mode::Altitude);
  s.flight.arm();
  s.flight.set_sticks({0, 0, 0, 0.8f});
  s.fly(3.0f);
  REQUIRE_FALSE(s.flight.on_ground());
  s.flight.set_sticks({0, 0, 0, 0.0f});  // full down: 1.5 m/s
  s.fly(15.0f);
  CHECK(s.plant.on_ground());
  CHECK(s.flight.on_ground());
  CHECK_FALSE(s.flight.armed());
}

TEST_CASE("the land detector waits for quiet before it calls a landing") {
  LandDetector d;
  d.update(true, 1.2f, -1.0f, 0.5f, 0.1f);  // climbing out
  CHECK_FALSE(d.landed());
  for (int k = 0; k < 5; ++k) d.update(true, 0.4f, 0.0f, 0.0f, 0.1f);
  CHECK_FALSE(d.landed());  // half a second isn't enough
  for (int k = 0; k < 6; ++k) d.update(true, 0.4f, 0.0f, 0.0f, 0.1f);
  CHECK(d.landed());
}

TEST_CASE("a 15 degree roll stick in altitude mode settles inside 5% within 0.5 s") {
  // the flight sim's steps scenario, on the host: PX4 (tuned) settles in 0.17 s
  Sim s;
  s.flight.set_mode(Mode::Altitude);
  s.flight.arm();
  s.flight.set_sticks({0, 0, 0, 0.8f});
  s.fly(3.0f);
  s.flight.set_sticks({0, 0, 0, 0.5f});
  s.fly(4.0f);
  const float stick = 15.0f / 35.0f;
  s.flight.set_sticks({stick, 0, 0, 0.5f});
  std::vector<float> roll;
  for (int k = 0; k < 500; ++k) {  // 2 s
    s.fly(kDt);
    roll.push_back(s.plant.q.roll() * 180 / kPi);
  }
  const float final = roll.back();
  int settled = 0;
  for (int k = static_cast<int>(roll.size()) - 1; k >= 0; --k) {
    if (std::abs(roll[static_cast<size_t>(k)] - final) > 0.05f * 15.0f) {
      settled = k + 1;
      break;
    }
  }
  const float settle_s = static_cast<float>(settled) * kDt;
  CHECK(final == Approx(15.0f).epsilon(0.07));
  CHECK(settle_s < 0.5f);
  MESSAGE("settles in " << settle_s << " s at " << final << " degrees");
}

TEST_CASE("armed long after power-on, it still gets its 10 s to take off") {
  Sim s;
  s.flight.set_mode(Mode::Altitude);
  s.fly(20.0f);  // sitting on the ground, disarmed, for 20 s
  s.flight.arm();
  s.flight.set_sticks({0, 0, 0, 0.5f});
  s.fly(5.0f);
  CHECK(s.flight.armed());  // not disarmed at once
  s.fly(6.0f);
  CHECK_FALSE(s.flight.armed());  // but after 10 s without taking off, it is
}
