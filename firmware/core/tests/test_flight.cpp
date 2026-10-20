// The flight loop in rate mode, flying the host's rigid-body quad.
#include <doctest/doctest.h>

#include <algorithm>
#include <array>
#include <cmath>
#include <string>

#include "pcs14/airframe_file.hpp"
#include "pcs14/flight.hpp"
#include "plant.hpp"

using namespace pcs14;
using doctest::Approx;

namespace {
constexpr float kDt = 1.0f / 250;  // the sim's IMU rate, which drives the loop there

std::array<float, 4> speeds(const Mix& m) { return m.rad_s; }

// flies `seconds` with the sticks as they are, and returns the largest tilt seen in degrees
float fly(Flight& flight, test::Plant& plant, float seconds) {
  float worst = 0;
  for (int k = 0; k < static_cast<int>(seconds / kDt); ++k) {
    const Mix m = flight.step(plant.rate, plant.accel(), kDt);
    plant.step(speeds(m), kDt);
    if (!plant.on_ground()) worst = std::max(worst, plant.q.tilt() * 180 / kPi);
  }
  return worst;
}
}  // namespace

TEST_CASE("disarmed the motors stop; armed with no throttle they idle") {
  Flight flight(test::base_airframe());
  test::Plant plant(test::base_airframe());
  Mix m = flight.step(plant.rate, plant.accel(), kDt);
  for (float w : m.rad_s) CHECK(w == 0.0f);
  flight.arm();
  m = flight.step(plant.rate, plant.accel(), kDt);
  for (float w : m.rad_s) CHECK(w == Approx(142.0f));
  flight.disarm();
  m = flight.step(plant.rate, plant.accel(), kDt);
  for (float w : m.rad_s) CHECK(w == 0.0f);
}

TEST_CASE("the hover throttle carries the weight") {
  Flight flight(test::base_airframe());
  CHECK(flight.hover_throttle() * flight.max_thrust() == Approx(1.86f * kG));
  CHECK(flight.hover_throttle() == Approx(0.32f).epsilon(0.02));
}

TEST_CASE("rate mode with the sticks centered takes off and stays level") {
  Flight flight(test::base_airframe());
  test::Plant plant(test::base_airframe());
  flight.arm();
  flight.set_sticks({0, 0, 0, flight.hover_throttle() * 1.15f});
  float worst = fly(flight, plant, 2.0f);
  CHECK_FALSE(plant.on_ground());
  flight.set_sticks({0, 0, 0, flight.hover_throttle()});
  worst = std::max(worst, fly(flight, plant, 10.0f));
  CHECK(worst < 1.0f);
  CHECK(-plant.position.z > 1.0f);
}

TEST_CASE("an off-center weight is held by the integrators, not by tilting further") {
  Flight flight(test::base_airframe());
  test::Plant plant(test::base_airframe());
  plant.cg_offset = {0.003f, -0.002f, 0};  // 3 mm forward and 2 left, past the CAD's balance check
  flight.arm();
  flight.set_sticks({0, 0, 0, flight.hover_throttle() * 1.15f});
  float worst = fly(flight, plant, 2.0f);
  flight.set_sticks({0, 0, 0, flight.hover_throttle()});
  worst = std::max(worst, fly(flight, plant, 10.0f));
  CHECK(worst < 5.0f);
  CHECK(std::abs(plant.rate.x) < 0.01f);
  CHECK(std::abs(plant.rate.y) < 0.01f);
}

TEST_CASE("a roll stick rolls right at the asked rate, and centering it stops the roll") {
  Flight flight(test::base_airframe());
  test::Plant plant(test::base_airframe());
  flight.arm();
  flight.set_sticks({0, 0, 0, flight.hover_throttle() * 1.15f});
  fly(flight, plant, 2.0f);
  flight.set_sticks({0.25f, 0, 0, flight.hover_throttle()});
  fly(flight, plant, 0.15f);
  const float asked = 0.25f * FlightGains{}.max_rate_roll_pitch;
  CHECK(plant.rate.x == Approx(asked).epsilon(0.1));
  flight.set_sticks({0, 0, 0, flight.hover_throttle()});
  fly(flight, plant, 1.0f);
  CHECK(std::abs(plant.rate.x) < 0.02f);
  CHECK(plant.q.roll() > 0.1f);  // it stays where it rolled to: rate mode doesn't self-level
}

TEST_CASE("a yaw stick turns the nose right") {
  Flight flight(test::base_airframe());
  test::Plant plant(test::base_airframe());
  flight.arm();
  flight.set_sticks({0, 0, 0, flight.hover_throttle() * 1.15f});
  fly(flight, plant, 2.0f);
  flight.set_sticks({0, 0, 0.3f, flight.hover_throttle()});
  fly(flight, plant, 1.0f);
  CHECK(plant.rate.z == Approx(0.3f * FlightGains{}.max_rate_yaw).epsilon(0.1));
}

TEST_CASE("the airframe file reads, and says what's wrong when it doesn't") {
  const std::string text =
      "# base\n"
      "mass_kg 1.86\n"
      "inertia_kg_m2 0.0125 0.0155 0.0233\n"
      "rotor 0.1484 0.1485 0.016\n"
      "rotor -0.1486 -0.1485 0.016\n"
      "rotor 0.1484 -0.1485 -0.016   # front left\n"
      "rotor -0.1486 0.1485 -0.016\n"
      "motor_constant 1.5777e-05\n"
      "idle_rad_s 142\n"
      "max_rad_s 947\n"
      "hover_rad_s 554  # a note for people, ignored\n";
  Airframe a;
  std::string error;
  REQUIRE(parse_airframe(text, a, error));
  CHECK(a.mass_kg == Approx(1.86f));
  CHECK(a.inertia.z == Approx(0.0233f));
  CHECK(a.mixer.rotors[2].y == Approx(-0.1485f));
  CHECK(a.mixer.rotors[2].km == Approx(-0.016f));
  CHECK(a.mixer.max_rad_s == Approx(947.0f));

  CHECK_FALSE(parse_airframe("mass_kg 1.86\n", a, error));
  CHECK(error == "missing inertia_kg_m2");
  CHECK_FALSE(parse_airframe("mass_kg 1.86 2\n", a, error));
  CHECK(error == "line 1: mass_kg takes one number");
  CHECK_FALSE(parse_airframe("mass_kg heavy\n", a, error));
  CHECK(error == "line 1: not a number after mass_kg");
}
