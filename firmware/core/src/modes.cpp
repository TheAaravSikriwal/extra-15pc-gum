// The flight modes' names on the wire and in the logs. GPL-3.0.
#include "pcs14/modes.hpp"

namespace pcs14 {

namespace {
struct Px4Mode {
  Mode mode;
  uint8_t main, sub, nav;
};
// nav_state numbers from PX4's vehicle_status message (the ones pcs14.flight.ulog reads)
constexpr Px4Mode kTable[] = {
    {Mode::Manual, px4::kStabilized, 0, 15},
    {Mode::Acro, px4::kAcro, 0, 10},
    {Mode::Altitude, px4::kAltitude, 0, 1},
    {Mode::Position, px4::kPosition, 0, 2},
    {Mode::Offboard, px4::kOffboard, 0, 14},
    {Mode::Takeoff, px4::kAuto, px4::kAutoTakeoff, 17},
    {Mode::Hold, px4::kAuto, px4::kAutoLoiter, 4},
    {Mode::Land, px4::kAuto, px4::kAutoLand, 18},
    {Mode::Return, px4::kAuto, px4::kAutoReturn, 5},
    // PX4 has no main mode for termination; it reports the last one with nav_state 13
    {Mode::Termination, px4::kAuto, px4::kAutoReady, 13},
};
}  // namespace

uint32_t px4_custom_mode(Mode mode) {
  for (const Px4Mode& m : kTable)
    if (m.mode == mode)
      return (static_cast<uint32_t>(m.main) << 16) | (static_cast<uint32_t>(m.sub) << 24);
  return 0;
}

bool mode_from_px4(uint8_t main_mode, uint8_t sub_mode, Mode& mode) {
  if (main_mode == px4::kManual) {  // PX4's manual is my manual: I always self-level
    mode = Mode::Manual;
    return true;
  }
  for (const Px4Mode& m : kTable) {
    if (m.mode == Mode::Termination) continue;  // asked for with its own command, not a mode
    if (m.main == main_mode && (main_mode != px4::kAuto || m.sub == sub_mode)) {
      mode = m.mode;
      return true;
    }
  }
  return false;
}

uint8_t nav_state(Mode mode) {
  for (const Px4Mode& m : kTable)
    if (m.mode == mode) return m.nav;
  return 0;
}

}  // namespace pcs14
