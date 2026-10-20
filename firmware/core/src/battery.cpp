// The fuel gauge. GPL-3.0.
#include "pcs14/battery.hpp"

namespace pcs14 {

float resting_cell_volts(const PackModel& pack, float share) {
  const auto& c = pack.curve;
  if (c.empty()) return 0;
  if (share <= c.front().first) return c.front().second;
  for (size_t k = 1; k < c.size(); ++k) {
    if (share <= c[k].first) {
      const float f = (share - c[k - 1].first) / (c[k].first - c[k - 1].first);
      return c[k - 1].second + f * (c[k].second - c[k - 1].second);
    }
  }
  return c.back().second;
}

void BatteryGauge::update(float volts, float amps, float dt) {
  if (dt <= 0) return;
  used_mah_ += amps * dt / 3.6f;  // A s to mAh
  if (pack_.series <= 0 || volts <= 0) return;
  const float cell = (volts + amps * pack_.resistance_ohm) / static_cast<float>(pack_.series);
  if (resting_cell_v_ < 0) {
    resting_cell_v_ = cell;
  } else {
    resting_cell_v_ += (cell - resting_cell_v_) * (dt / (smoothing_s_ + dt));
  }
}

float BatteryGauge::by_count() const {
  if (pack_.capacity_mah <= 0) return -1;
  const float left = 1 - used_mah_ / pack_.capacity_mah;
  return left < 0 ? 0 : left;
}

float BatteryGauge::by_voltage() const {
  const auto& c = pack_.curve;
  if (c.size() < 2 || resting_cell_v_ < 0) return -1;
  // the curve rises with the share, so it inverts piece by piece
  if (resting_cell_v_ <= c.front().second) return c.front().first;
  for (size_t k = 1; k < c.size(); ++k) {
    if (resting_cell_v_ <= c[k].second) {
      const float f = (resting_cell_v_ - c[k - 1].second) / (c[k].second - c[k - 1].second);
      return c[k - 1].first + f * (c[k].first - c[k - 1].first);
    }
  }
  return c.back().first;
}

float BatteryGauge::remaining() const {
  const float count = by_count(), voltage = by_voltage();
  if (count < 0) return voltage;
  if (voltage < 0) return count;
  return voltage < count ? voltage : count;
}

}  // namespace pcs14
