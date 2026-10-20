// The fuel gauge (step 5, task 9): charge counted in mAh, the resting voltage as a backup.
#include <doctest/doctest.h>

#include "pcs14/battery.hpp"

using namespace pcs14;
using doctest::Approx;

namespace {
// a 6S2P pack like the build's: 9000 mAh, 51 mOhm, and a made-up resting curve per cell
PackModel pack() {
  PackModel m;
  m.capacity_mah = 9000;
  m.series = 6;
  m.resistance_ohm = 0.051f;
  m.curve = {{0.0f, 3.0f}, {0.2f, 3.45f}, {0.5f, 3.65f}, {0.8f, 3.95f}, {1.0f, 4.2f}};
  return m;
}
// the pack's terminal voltage at `share` charge and `amps`, by the same model
float terminal(float share, float amps) {
  return 6 * resting_cell_volts(pack(), share) - amps * 0.051f;
}
void run(BatteryGauge& g, float share, float amps, float seconds) {
  for (float t = 0; t < seconds; t += 0.1f) g.update(terminal(share, amps), amps, 0.1f);
}
}  // namespace

TEST_CASE("the charge used is counted, and the share left follows it") {
  BatteryGauge g(pack());
  run(g, 0.9f, 18.0f, 15 * 60.0f);  // 18 A for a quarter hour: 4500 mAh
  CHECK(g.used_mah() == Approx(4500).epsilon(0.002));
  CHECK(g.by_count() == Approx(0.5f).epsilon(0.002));
}

TEST_CASE("the resting voltage looks through the sag under load") {
  BatteryGauge g(pack());
  run(g, 0.5f, 0.0f, 10.0f);
  const float at_rest = g.by_voltage();
  run(g, 0.5f, 60.0f, 10.0f);  // 3 V of sag at 60 A
  CHECK(g.by_voltage() == Approx(at_rest).epsilon(0.02));
  CHECK(at_rest == Approx(0.5f).epsilon(0.02));
}

TEST_CASE("when the voltage says less than the count, the voltage wins") {
  // a pack that has lost capacity: the count still thinks it's two thirds full, the cells say 20%
  BatteryGauge g(pack());
  run(g, 0.2f, 18.0f, 20 * 60.0f);  // 6000 mAh counted
  CHECK(g.by_count() == Approx(1 - 6000.0f / 9000).epsilon(0.01));
  CHECK(g.remaining() == Approx(0.2f).epsilon(0.05));
}

TEST_CASE("the voltage only pulls it down: a healthy count isn't raised by a rested pack") {
  BatteryGauge g(pack());
  run(g, 0.9f, 18.0f, 20 * 60.0f);  // the count says 33%, the cells (made up) say 90%
  CHECK(g.remaining() == Approx(g.by_count()));
}

TEST_CASE("without a capacity it goes by the voltage, and without either it doesn't know") {
  PackModel m = pack();
  m.capacity_mah = 0;
  BatteryGauge g(m);
  run(g, 0.5f, 10.0f, 10.0f);
  CHECK(g.by_count() < 0.0f);
  CHECK(g.remaining() == Approx(0.5f).epsilon(0.03));
  BatteryGauge none(PackModel{});
  none.update(24.0f, 10.0f, 0.1f);
  CHECK(none.remaining() < 0.0f);
}
