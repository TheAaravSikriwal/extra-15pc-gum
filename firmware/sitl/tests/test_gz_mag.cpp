// Gazebo's magnetometer, put right: against readings taken from static models on 2026-10-20.
#include <doctest/doctest.h>

#include <cmath>

#include "../src/gz_mag.hpp"

using namespace pcs14;
using doctest::Approx;

namespace {
// Zurich's field, north-east-down, as Gazebo's readings imply it (gauss)
const Vec3 kField{0.2162f, -0.0097f, 0.4294f};
// what the body should feel at `q` (forward-right-down to north-east-down)
Vec3 expected(const Quat& q) { return q.unrotate(kField); }
constexpr float kDeg = kPi / 180;
}  // namespace

TEST_CASE("level, it's PX4's fixed mapping") {
  const Quat east = Quat::from_euler(0, 0, 90 * kDeg);  // the models spawn facing east
  const Vec3 b = sim::gazebo_magnetometer({0.2162f, 0.0097f, 0.4294f}, east);
  CHECK(b.x == Approx(-0.0097f).epsilon(0.01));  // (-y, -x, z)
  CHECK(b.y == Approx(-0.2162f).epsilon(0.01));
  CHECK(b.z == Approx(0.4294f).epsilon(0.01));
}

TEST_CASE("pitched and rolled, it matches the field the body really feels") {
  // nose down 30 degrees, facing east: Gazebo read (-0.0275, 0.0098, 0.48)
  const Quat pitched = Quat::from_euler(0, -30 * kDeg, 90 * kDeg);
  Vec3 b = sim::gazebo_magnetometer({-0.0275f, 0.0098f, 0.48f}, pitched);
  Vec3 want = expected(pitched);
  CHECK(b.x == Approx(want.x).epsilon(0.02));
  CHECK(b.y == Approx(want.y).epsilon(0.02));
  CHECK(b.z == Approx(want.z).epsilon(0.02));
  // right side down 30 degrees, facing east: Gazebo read (0.2162, 0.2231, 0.367)
  const Quat rolled = Quat::from_euler(30 * kDeg, 0, 90 * kDeg);
  b = sim::gazebo_magnetometer({0.2162f, 0.2231f, 0.367f}, rolled);
  want = expected(rolled);
  CHECK(b.x == Approx(want.x).epsilon(0.02));
  CHECK(b.y == Approx(want.y).epsilon(0.02));
  CHECK(b.z == Approx(want.z).epsilon(0.02));
}
