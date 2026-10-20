// The attitude estimator: settling from a wrong start, following a turn, ignoring hard pulls.
#include <doctest/doctest.h>

#include "pcs14/attitude.hpp"

using namespace pcs14;
using doctest::Approx;

namespace {
constexpr float kDt = 1.0f / 250;  // the IMU's rate in the sim
const Vec3 kStill{0, 0, -kG};      // what a level, still IMU feels: specific force, up in FRD
const Vec3 kMagNorth{0.2f, 0, 0.45f};  // a field pointing north and down, in the world frame

Vec3 body_of(const Quat& q, const Vec3& world) { return q.unrotate(world); }
}  // namespace

TEST_CASE("from a wrong guess it settles to level on a still IMU") {
  Attitude att;
  att.reset(Quat::from_euler(0.35f, -0.2f, 0));  // 20 and 11 degrees off
  for (int k = 0; k < 250 * 10; ++k) att.update({0, 0, 0}, kStill, nullptr, kDt);
  CHECK(std::abs(att.q().roll()) < 0.0175f);  // under a degree after 10 s
  CHECK(std::abs(att.q().pitch()) < 0.0175f);
}

TEST_CASE("it follows a steady yaw turn on the gyro alone") {
  Attitude att;
  const float rate = 0.5f;  // rad/s
  for (int k = 0; k < 250 * 2; ++k) att.update({0, 0, rate}, kStill, nullptr, kDt);
  CHECK(att.q().yaw() == Approx(1.0f).epsilon(0.01));
}

TEST_CASE("the magnetometer pulls the heading to north") {
  Attitude att;
  att.reset(Quat::from_euler(0, 0, 0.5f));  // guessing 29 degrees east of the truth
  const Quat truth{};                       // level, facing north
  for (int k = 0; k < 250 * 20; ++k) {
    const Vec3 mag = body_of(truth, kMagNorth);
    att.update({0, 0, 0}, kStill, &mag, kDt);
  }
  CHECK(std::abs(att.q().yaw()) < 0.035f);  // inside 2 degrees
}

TEST_CASE("a hard pull doesn't drag the tilt with it") {
  Attitude att;
  // level, but pulling 3 g in a turn: the accelerometer's direction is no help, so it's ignored
  for (int k = 0; k < 250; ++k) att.update({0, 0, 0}, {6 * kG, 0, -kG}, nullptr, kDt);
  CHECK(att.q().tilt() < 0.01f);
}

TEST_CASE("a gyro bias is learned and taken out") {
  Attitude att;
  const Vec3 bias{0.02f, -0.015f, 0};  // rad/s, a typical MEMS gyro's offset
  for (int k = 0; k < 250 * 60; ++k) att.update(bias, kStill, nullptr, kDt);
  CHECK(std::abs(att.q().roll()) < 0.01f);
  CHECK(std::abs(att.q().pitch()) < 0.01f);
  CHECK(att.bias().x == Approx(bias.x).epsilon(0.1));
  CHECK(att.bias().y == Approx(bias.y).epsilon(0.1));
}
