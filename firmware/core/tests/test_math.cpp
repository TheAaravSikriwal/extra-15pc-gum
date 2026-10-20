// Rotations worked by hand, in PX4's frames: forward-right-down body, north-east-down world.
#include <doctest/doctest.h>

#include "pcs14/math.hpp"

using namespace pcs14;
using doctest::Approx;

TEST_CASE("a quarter turn of yaw points the nose east") {
  const Quat q = Quat::from_euler(0, 0, kPi / 2);  // yaw is clockwise seen from above, in NED
  const Vec3 nose = q.rotate({1, 0, 0});
  CHECK(nose.x == Approx(0).epsilon(1e-6));
  CHECK(nose.y == Approx(1));
  CHECK(nose.z == Approx(0).epsilon(1e-6));
}

TEST_CASE("rolling right puts the right wing down") {
  const Quat q = Quat::from_euler(0.3f, 0, 0);
  const Vec3 right = q.rotate({0, 1, 0});
  CHECK(right.z > 0.0f);  // down is +z in NED
  CHECK(right.z == Approx(std::sin(0.3f)));
}

TEST_CASE("pitching up raises the nose") {
  const Quat q = Quat::from_euler(0, 0.2f, 0);
  CHECK(q.rotate({1, 0, 0}).z == Approx(-std::sin(0.2f)));
}

TEST_CASE("the angles come back out") {
  const Quat q = Quat::from_euler(0.1f, -0.25f, 2.0f);
  CHECK(q.roll() == Approx(0.1f));
  CHECK(q.pitch() == Approx(-0.25f));
  CHECK(q.yaw() == Approx(2.0f));
  // the tilt doesn't care about the heading
  CHECK(Quat::from_euler(0, 0.5f, 1.3f).tilt() == Approx(0.5f));
}

TEST_CASE("unrotating undoes rotating") {
  const Quat q = Quat::from_euler(0.4f, 0.2f, -1.0f);
  const Vec3 v{0.3f, -2.0f, 5.0f};
  const Vec3 back = q.unrotate(q.rotate(v));
  CHECK(back.x == Approx(v.x));
  CHECK(back.y == Approx(v.y));
  CHECK(back.z == Approx(v.z));
}

TEST_CASE("angles wrap into one turn") {
  CHECK(wrap_pi(3 * kPi / 2) == Approx(-kPi / 2));
  CHECK(wrap_pi(-3 * kPi / 2) == Approx(kPi / 2));
}
