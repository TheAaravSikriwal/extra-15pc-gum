// pcs14_monitor_replay: the safety monitor's triggers over recorded IMU samples, for checking
// them against the Python reference (tests/check_triggers.py). GPL-3.0.
//
// Reads "t ax ay az gx gy gz tilt" lines on stdin (s, m/s^2, rad/s, rad: the tilt as the
// reference takes it, an input), and prints one line per trigger: "<kind> <at> <since>".
#include <cstdio>
#include <iostream>
#include <sstream>
#include <string>
#include <vector>

#include "pcs14/monitor.hpp"

int main() {
  pcs14::TriggerWatch watch;
  std::vector<pcs14::Trigger> fired;
  std::string line;
  while (std::getline(std::cin, line)) {
    std::istringstream w(line);
    double t;
    float ax, ay, az, gx, gy, gz, tilt;
    if (!(w >> t >> ax >> ay >> az >> gx >> gy >> gz >> tilt)) continue;
    fired.clear();
    watch.update(t, {ax, ay, az}, {gx, gy, gz}, tilt, fired);
    for (const auto& f : fired)
      std::printf("%s %.6f %.6f\n", pcs14::trigger_name(f.kind), f.at, f.since);
  }
  return 0;
}
