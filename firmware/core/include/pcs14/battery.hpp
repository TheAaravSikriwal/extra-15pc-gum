// The fuel gauge: how much charge is left. GPL-3.0.
//
// Decided in the safety basics: the low-battery failsafe counts mAh used, with the voltage as a
// backup, because a Li-ion pack's flat curve and its sag under load make voltage a poor fuel
// gauge on its own. So the gauge counts the current over time, and also reads the charge off
// the cells' resting-voltage curve (the terminal voltage plus the current times the pack's
// resistance, smoothed), the same curve the sizing model flies on. The answer is the count,
// unless the voltage says less: a pack that has lost capacity, or a current sensor reading
// low, shows up there first. The voltage never raises the count, since a pack that just
// stopped working hard reads high for a while.
//
// On the drone the current comes from the ESC's telemetry and the voltage from the flight
// controller's ADC. In the flight sim the failsafe goes by PX4's simulated battery instead, so
// the low battery scenario means the same for both firmwares.
#pragma once

#include <utility>
#include <vector>

namespace pcs14 {

struct PackModel {
  float capacity_mah = 0;  // 0 is unknown: then the count can't give a share
  int series = 6;
  float resistance_ohm = 0;  // the whole pack's, wiring included
  // the resting voltage of one cell against the share of charge left, the share rising
  std::vector<std::pair<float, float>> curve;
};

// a cell's resting voltage at `share` charge, by the pack's curve (clamped at its ends)
float resting_cell_volts(const PackModel& pack, float share);

class BatteryGauge {
 public:
  explicit BatteryGauge(PackModel pack, float smoothing_s = 2.0f)
      : pack_(std::move(pack)), smoothing_s_(smoothing_s) {}

  // the pack's terminal voltage (V), the current out of it (A) and the step (s)
  void update(float volts, float amps, float dt);

  float used_mah() const { return used_mah_; }
  float by_count() const;    // the share left by the count, or -1 without a capacity
  float by_voltage() const;  // the share left by the resting voltage, or -1 without a curve
  float remaining() const;   // the lower of the two it knows, or -1 when it knows neither

 private:
  PackModel pack_;
  float smoothing_s_;
  float used_mah_ = 0;
  float resting_cell_v_ = -1;
};

}  // namespace pcs14
