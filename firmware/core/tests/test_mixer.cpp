// The mixer: torques and thrust into each rotor's thrust and speed, on the generator's quad X.
#include <doctest/doctest.h>

#include <cmath>

#include "pcs14/mixer.hpp"

using namespace pcs14;
using doctest::Approx;

namespace {
// PX4's quad X order, in its frame (x forward, y right): front right and back left turn
// counterclockwise (km > 0), front left and back right clockwise. The arm is 0.21 m.
constexpr float a = 0.1485f;
MixerSetup setup() {
  MixerSetup s;
  s.rotors = {{{a, a, 0.016f}, {-a, -a, 0.016f}, {a, -a, -0.016f}, {-a, a, -0.016f}}};
  s.motor_constant = 1.5777e-5f;  // N / (rad/s)^2, the flight sim's fit
  s.idle_rad_s = 139.0f;
  s.max_rad_s = 925.0f;
  return s;
}
// what each rotor's thrust does to the body: torque about each axis and the total
void forces(const MixerSetup& s, const Mix& m, Vec3& torque, float& thrust) {
  torque = {};
  thrust = 0;
  for (int i = 0; i < 4; ++i) {
    const Rotor& r = s.rotors[i];
    torque += Vec3{-r.y * m.thrust[i], r.x * m.thrust[i], r.km * m.thrust[i]};
    thrust += m.thrust[i];
  }
}
}  // namespace

TEST_CASE("a plain hover splits the thrust evenly") {
  Mixer mixer(setup());
  const Mix m = mixer.mix({0, 0, 0}, 20.0f);
  for (int i = 0; i < 4; ++i) CHECK(m.thrust[i] == Approx(5.0f));
  // speed from thrust = k w^2
  CHECK(m.rad_s[0] == Approx(std::sqrt(5.0f / 1.5777e-5f)));
  CHECK_FALSE(m.saturated);
}

TEST_CASE("the mix makes exactly the torques and thrust asked for") {
  Mixer mixer(setup());
  const Vec3 wanted{0.3f, -0.2f, 0.05f};  // N m
  const Mix m = mixer.mix(wanted, 22.0f);
  Vec3 torque;
  float thrust;
  forces(setup(), m, torque, thrust);
  CHECK(torque.x == Approx(wanted.x));
  CHECK(torque.y == Approx(wanted.y));
  CHECK(torque.z == Approx(wanted.z));
  CHECK(thrust == Approx(22.0f));
}

TEST_CASE("rolling right speeds up the left rotors") {
  Mixer mixer(setup());
  const Mix m = mixer.mix({0.5f, 0, 0}, 20.0f);
  // the left rotors (y < 0) are 1 and 2
  CHECK(m.thrust[1] > m.thrust[0]);
  CHECK(m.thrust[2] > m.thrust[3]);
}

TEST_CASE("when the motors run out, yaw goes first and roll and pitch stay") {
  Mixer mixer(setup());
  const Vec3 wanted{0.4f, 0.3f, 3.0f};  // far more yaw than the props can give
  const Mix m = mixer.mix(wanted, 20.0f);
  CHECK(m.saturated);
  Vec3 torque;
  float thrust;
  forces(setup(), m, torque, thrust);
  CHECK(torque.x == Approx(wanted.x).epsilon(0.01));
  CHECK(torque.y == Approx(wanted.y).epsilon(0.01));
  CHECK(torque.z < wanted.z);
  const float top = 1.5777e-5f * 925.0f * 925.0f, idle = 1.5777e-5f * 139.0f * 139.0f;
  for (float t : m.thrust) {
    CHECK(t <= top + 1e-4f);
    CHECK(t >= idle - 1e-4f);
  }
}

TEST_CASE("flat out, thrust gives way so roll and pitch can still act") {
  Mixer mixer(setup());
  const float top = 1.5777e-5f * 925.0f * 925.0f;
  const Mix m = mixer.mix({0.6f, 0, 0}, 4 * top);  // full thrust and a roll on top
  Vec3 torque;
  float thrust;
  forces(setup(), m, torque, thrust);
  CHECK(m.saturated);
  CHECK(torque.x == Approx(0.6f).epsilon(0.01));
  CHECK(thrust < 4 * top);
}
