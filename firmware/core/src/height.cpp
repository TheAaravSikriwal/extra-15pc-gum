// The height filter. GPL-3.0.
#include "pcs14/height.hpp"

#include <cmath>

namespace pcs14 {

float pressure_height(float pressure_pa, float reference_pa) {
  // the troposphere's standard atmosphere, the barometric formula PX4 uses too
  return 44330.0f * (1.0f - std::pow(pressure_pa / reference_pa, 0.190295f));
}

void HeightFilter::predict(float specific_force_down, float dt) {
  // at rest the accelerometer feels -g along down, so the acceleration is that plus g
  const float a = specific_force_down + kG - bias_;
  z_ += vz_ * dt + 0.5f * a * dt * dt;
  vz_ += a * dt;
}

void HeightFilter::correct(float z_measured, float dt) {
  const float e = z_measured - z_;
  z_ += 3 * w_ * e * dt;
  vz_ += 3 * w_ * w_ * e * dt;
  bias_ -= w_ * w_ * w_ * e * dt;
}

}  // namespace pcs14
