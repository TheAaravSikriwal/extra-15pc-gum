// The modes' names on the wire, against PX4's encoding as MAVSDK decodes it.
#include <doctest/doctest.h>

#include <initializer_list>

#include "pcs14/modes.hpp"

using namespace pcs14;

TEST_CASE("custom_mode carries PX4's main mode in bits 16 to 23 and the sub mode above") {
  CHECK(px4_custom_mode(Mode::Position) == (3u << 16));
  CHECK(px4_custom_mode(Mode::Offboard) == (6u << 16));
  CHECK(px4_custom_mode(Mode::Hold) == ((4u << 16) | (3u << 24)));
  CHECK(px4_custom_mode(Mode::Land) == ((4u << 16) | (6u << 24)));
  CHECK(px4_custom_mode(Mode::Return) == ((4u << 16) | (5u << 24)));
}

TEST_CASE("each mode MAVSDK can ask for comes back as itself") {
  for (Mode m : {Mode::Manual, Mode::Acro, Mode::Altitude, Mode::Position, Mode::Offboard,
                 Mode::Takeoff, Mode::Hold, Mode::Land, Mode::Return}) {
    const uint32_t c = px4_custom_mode(m);
    Mode back{};
    REQUIRE(mode_from_px4(static_cast<uint8_t>(c >> 16), static_cast<uint8_t>(c >> 24), back));
    CHECK(back == m);
  }
  Mode m{};
  CHECK(mode_from_px4(px4::kManual, 0, m));
  CHECK(m == Mode::Manual);
  CHECK_FALSE(mode_from_px4(px4::kAuto, px4::kAutoMission, m));  // no missions yet
  CHECK_FALSE(mode_from_px4(42, 0, m));
}

TEST_CASE("the logs number the modes the way the graders read them") {
  CHECK(nav_state(Mode::Hold) == 4);
  CHECK(nav_state(Mode::Return) == 5);
  CHECK(nav_state(Mode::Termination) == 13);
  CHECK(nav_state(Mode::Offboard) == 14);
  CHECK(nav_state(Mode::Takeoff) == 17);
  CHECK(nav_state(Mode::Land) == 18);
}
