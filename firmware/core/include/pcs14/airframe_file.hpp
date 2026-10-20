// Reading an airframe from a text file, the way the sim gets it. GPL-3.0.
//
// The flight sim's generator writes one per module combination (firmware.txt, next to the
// Gazebo model), from the same numbers as the model: one "key values..." line each, and # for
// comments. On the drone the same numbers come from parameters instead.
//
//   mass_kg 1.86
//   inertia_kg_m2 0.0125 0.0155 0.0233
//   rotor 0.1484 0.1485 0.016          (x forward, y right, km; one line per rotor, in order)
//   motor_constant 1.5777e-05
//   idle_rad_s 142
//   max_rad_s 947
#pragma once

#include <string>

#include "pcs14/flight.hpp"

namespace pcs14 {

// Fills `airframe` from the file's text. Returns false, with `error` saying why, when a line
// doesn't read or something is missing.
bool parse_airframe(const std::string& text, Airframe& airframe, std::string& error);

}  // namespace pcs14
