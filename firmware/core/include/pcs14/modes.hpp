// The flight modes, and how PX4 names them on the wire and in its logs, so MAVSDK, QGroundControl
// and the flight sim's graders read my firmware's modes as PX4's. GPL-3.0.
//
// On MAVLink, PX4 puts its mode in HEARTBEAT's custom_mode: a main mode in bits 16 to 23 and,
// for the automatic modes, a sub mode in bits 24 to 31 (PX4's px4_custom_mode.h, which MAVSDK
// copies). In its logs, vehicle_status.nav_state numbers them differently again.
#pragma once

#include <cstdint>

namespace pcs14 {

enum class Mode : uint8_t {
  Manual,      // self-level on the sticks, throttle direct
  Acro,        // rate mode: the sticks ask for body rates
  Altitude,    // self-level, the throttle stick asks for a climb rate
  Position,    // the sticks ask for velocities, centered holds the spot
  Offboard,    // the companion computer (or the flight sim's script) sends setpoints
  Takeoff,     // climb to the take-off height, then hold
  Hold,        // hold the spot
  Land,        // come straight down and disarm
  Return,      // climb, fly home, land
  Termination  // motors off, chute out
};

// PX4's main modes and its automatic sub modes
namespace px4 {
constexpr uint8_t kManual = 1, kAltitude = 2, kPosition = 3, kAuto = 4, kAcro = 5,
                  kOffboard = 6, kStabilized = 7;
constexpr uint8_t kAutoReady = 1, kAutoTakeoff = 2, kAutoLoiter = 3, kAutoMission = 4,
                  kAutoReturn = 5, kAutoLand = 6;
}  // namespace px4

// HEARTBEAT's custom_mode for a mode
uint32_t px4_custom_mode(Mode mode);
// the mode a custom_mode asks for (as in MAV_CMD_DO_SET_MODE's main and sub mode), or false
// for one my firmware doesn't fly
bool mode_from_px4(uint8_t main_mode, uint8_t sub_mode, Mode& mode);
// vehicle_status.nav_state in PX4's logs
uint8_t nav_state(Mode mode);

}  // namespace pcs14
