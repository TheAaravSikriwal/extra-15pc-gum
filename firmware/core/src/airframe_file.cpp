// Reading an airframe file. GPL-3.0.
#include "pcs14/airframe_file.hpp"

#include <sstream>
#include <vector>

namespace pcs14 {

bool parse_airframe(const std::string& text, Airframe& airframe, std::string& error) {
  Airframe out;
  int rotors = 0;
  bool mass = false, inertia = false, k = false, idle = false, top = false;
  std::istringstream lines(text);
  std::string line;
  int number = 0;
  while (std::getline(lines, line)) {
    ++number;
    const auto hash = line.find('#');
    if (hash != std::string::npos) line.erase(hash);
    std::istringstream words(line);
    std::string key;
    if (!(words >> key)) continue;
    std::vector<float> values;
    float v;
    while (words >> v) values.push_back(v);
    if (!words.eof()) {
      error = "line " + std::to_string(number) + ": not a number after " + key;
      return false;
    }
    auto want = [&](size_t n) {
      if (values.size() == n) return true;
      error = "line " + std::to_string(number) + ": " + key + " takes " +
              (n == 1 ? std::string("one number") : std::to_string(n) + " numbers");
      return false;
    };
    if (key == "mass_kg") {
      if (!want(1)) return false;
      out.mass_kg = values[0];
      mass = true;
    } else if (key == "inertia_kg_m2") {
      if (!want(3)) return false;
      out.inertia = {values[0], values[1], values[2]};
      inertia = true;
    } else if (key == "rotor") {
      if (!want(3)) return false;
      if (rotors == 4) {
        error = "line " + std::to_string(number) + ": more than four rotors";
        return false;
      }
      out.mixer.rotors[static_cast<size_t>(rotors++)] = {values[0], values[1], values[2]};
    } else if (key == "motor_constant") {
      if (!want(1)) return false;
      out.mixer.motor_constant = values[0];
      k = true;
    } else if (key == "idle_rad_s") {
      if (!want(1)) return false;
      out.mixer.idle_rad_s = values[0];
      idle = true;
    } else if (key == "max_rad_s") {
      if (!want(1)) return false;
      out.mixer.max_rad_s = values[0];
      top = true;
    }
    // anything else is for someone else (the file also carries notes for people)
  }
  const char* missing = !mass        ? "mass_kg"
                        : !inertia   ? "inertia_kg_m2"
                        : rotors < 4 ? "rotor (four of them)"
                        : !k         ? "motor_constant"
                        : !idle      ? "idle_rad_s"
                        : !top       ? "max_rad_s"
                                     : nullptr;
  if (missing != nullptr) {
    error = std::string("missing ") + missing;
    return false;
  }
  airframe = out;
  return true;
}

}  // namespace pcs14
