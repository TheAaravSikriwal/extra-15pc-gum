// The position filter, the position controller and the automatic modes (step 5, task 8), on
// the host's rigid-body quad with a barometer and a GPS.
#include <doctest/doctest.h>

#include <algorithm>
#include <cmath>
#include <random>

#include "pcs14/flight.hpp"
#include "pcs14/position.hpp"
#include "plant.hpp"

using namespace pcs14;
using doctest::Approx;

namespace {
constexpr float kDt = 1.0f / 250;
constexpr int kBaroEvery = 5;  // 50 Hz
constexpr int kGpsEvery = 25;  // 10 Hz

struct Sim {
  Flight flight;
  test::Plant plant;
  std::mt19937 rng{11};
  std::normal_distribution<float> baro_noise{0.0f, 3.0f};  // Pa
  std::normal_distribution<float> gps_noise{0.0f, 0.05f};  // m
  int k = 0;
  float worst_tilt = 0;

  Sim() : flight(test::base_airframe()), plant(test::base_airframe()) {
    fly(1.0f);  // the filters find their feet before anything happens
  }

  void fly(float seconds) {
    for (int n = 0; n < static_cast<int>(seconds / kDt); ++n, ++k) {
      if (k % kBaroEvery == 0)
        flight.on_baro(plant.pressure() + baro_noise(rng), kDt * kBaroEvery);
      if (k % kGpsEvery == 0)
        flight.on_gps(plant.position.x + gps_noise(rng), plant.position.y + gps_noise(rng),
                      plant.velocity, kDt * kGpsEvery);
      const Mix m = flight.step(plant.rate, plant.accel(), kDt);
      plant.step(m.rad_s, kDt);
      if (!plant.on_ground()) worst_tilt = std::max(worst_tilt, plant.q.tilt() * 180 / kPi);
    }
  }
  // flies until `done` or `limit` seconds pass; returns whether it got there
  template <typename F>
  bool until(F done, float limit) {
    for (float t = 0; t < limit; t += 0.1f) {
      if (done()) return true;
      fly(0.1f);
    }
    return done();
  }
  float height() const { return -plant.position.z; }
};
}  // namespace

TEST_CASE("the thrust vector's attitude: level for straight up, tipped toward the push") {
  const Quat level = attitude_from_down({0, 0, 1}, 0.3f);
  CHECK(level.tilt() == Approx(0.0f).epsilon(1e-6));
  CHECK(level.yaw() == Approx(0.3f));
  // pushing north means the thrust leans north: the nose goes down
  const Quat forward = attitude_from_down(Vec3{-1, 0, 5}.normalized(), 0);
  CHECK(forward.pitch() < 0.0f);
  CHECK(forward.tilt() == Approx(std::atan2(1.0f, 5.0f)));
}

TEST_CASE("the position filter follows the GPS and learns the accelerometer's bias") {
  PositionFilter f;
  float p = 0, v = 0;
  for (int k = 0; k < 250 * 60; ++k) {
    const float t = static_cast<float>(k) * kDt;
    const float a = t > 20 && t < 22 ? 1.0f : (t > 22 && t < 24 ? -1.0f : 0.0f);
    v += a * kDt;
    p += v * kDt;
    f.predict(a + 0.2f, 0, kDt);  // the accelerometer reads 0.2 m/s^2 high
    if (k % kGpsEvery == 0) f.correct(p, 0, v, 0, kDt * kGpsEvery);
  }
  CHECK(f.north() == Approx(p).epsilon(0.01));
  CHECK(f.v_north() == Approx(v).epsilon(0.02));
}

TEST_CASE("the automatic modes wait for a position") {
  Flight flight(test::base_airframe());
  CHECK_FALSE(flight.set_mode(Mode::Hold));
  CHECK(flight.set_mode(Mode::Altitude));
}

TEST_CASE("take-off climbs to the take-off height and holds there") {
  Sim s;
  AutoSettings a;
  a.takeoff_height = 5.0f;
  s.flight.set_auto(a);
  s.flight.set_mode(Mode::Position);
  s.flight.arm();
  REQUIRE(s.flight.set_mode(Mode::Takeoff));
  REQUIRE(s.until([&] { return s.flight.mode() == Mode::Hold; }, 15.0f));
  CHECK(s.height() == Approx(5.0f).epsilon(0.1));
  const float held = s.height();
  float low = held, high = held, drift = 0;
  for (int k = 0; k < 100; ++k) {
    s.fly(0.1f);
    low = std::min(low, s.height());
    high = std::max(high, s.height());
    drift = std::max(drift, std::hypot(s.plant.position.x, s.plant.position.y));
  }
  CHECK(high - low < 0.5f);
  CHECK(drift < 0.5f);
  CHECK(s.worst_tilt < 5.0f);
}

TEST_CASE("offboard flies to a point, and holds when the setpoints stop") {
  Sim s;
  s.flight.set_mode(Mode::Position);
  s.flight.arm();
  s.flight.set_mode(Mode::Takeoff);
  REQUIRE(s.until([&] { return s.flight.mode() == Mode::Hold; }, 15.0f));
  OffboardTarget target;
  target.point = {20, -10, -8};
  bool started = false;
  const bool reached = s.until(
      [&] {
        s.flight.set_offboard(target);  // streamed, as offboard control has to be
        if (!started) started = s.flight.set_mode(Mode::Offboard);
        const Vec3 off = s.plant.position - target.point;
        return off.norm() < 0.5f && s.plant.velocity.norm() < 0.3f;
      },
      30.0f);
  CHECK(started);
  CHECK(reached);
  const Vec3 there = s.plant.position;
  s.fly(5.0f);  // no setpoints for 5 s
  CHECK((s.plant.position - there).norm() < 0.5f);
}

TEST_CASE("return climbs, flies home and lands there, then disarms") {
  Sim s;
  AutoSettings a;
  a.return_height = 15.0f;
  a.cruise_speed = 8.0f;
  s.flight.set_auto(a);
  s.flight.set_mode(Mode::Position);
  s.flight.arm();
  s.flight.set_mode(Mode::Takeoff);
  REQUIRE(s.until([&] { return s.flight.mode() == Mode::Hold; }, 15.0f));
  OffboardTarget out;
  out.point = {40, 15, -10};
  bool started = false;
  REQUIRE(s.until(
      [&] {
        s.flight.set_offboard(out);
        if (!started) started = s.flight.set_mode(Mode::Offboard);
        return (s.plant.position - out.point).norm() < 1.0f;
      },
      40.0f));
  REQUIRE(s.flight.set_mode(Mode::Return));
  float highest = 0;
  const bool home = s.until(
      [&] {
        highest = std::max(highest, s.height());
        return !s.flight.armed();
      },
      120.0f);
  CHECK(home);
  CHECK(highest == Approx(15.0f).epsilon(0.1));
  CHECK(std::hypot(s.plant.position.x, s.plant.position.y) < 1.0f);
  CHECK(s.plant.on_ground());
  CHECK(s.worst_tilt < 45.5f);
}

TEST_CASE("land comes straight down and disarms") {
  Sim s;
  AutoSettings a;
  a.takeoff_height = 12.0f;
  s.flight.set_auto(a);
  s.flight.set_mode(Mode::Position);
  s.flight.arm();
  s.flight.set_mode(Mode::Takeoff);
  REQUIRE(s.until([&] { return s.flight.mode() == Mode::Hold; }, 20.0f));
  REQUIRE(s.flight.set_mode(Mode::Land));
  float fastest = 0;
  const bool down = s.until(
      [&] {
        fastest = std::max(fastest, s.plant.velocity.z);
        return !s.flight.armed();
      },
      60.0f);
  CHECK(down);
  CHECK(fastest < 1.8f);  // 1.5 m/s up high, the land speed near the ground
  CHECK(std::hypot(s.plant.position.x, s.plant.position.y) < 0.5f);
}
