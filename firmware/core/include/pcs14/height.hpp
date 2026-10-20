// The height filter: the barometer's height and the accelerometer's push, blended. GPL-3.0.
//
// The accelerometer, turned into the world frame, says how the vertical speed is changing,
// smoothly and right away, but it drifts: integrate a small bias twice and the height runs
// off. The barometer says where the drone is without drifting, but it's noisy and slow. The
// filter integrates the accelerometer and pulls the result toward the barometer, and it learns
// the accelerometer's bias from how far it keeps having to pull. That's a third-order
// complementary filter: with gains 3w, 3w^2 and w^3 its error dies away like (s + w)^3, so one
// number, the crossover w, sets how much it trusts each sensor.
//
// Down is positive, like the rest of the firmware (north-east-down); the height is minus z.
#pragma once

#include "pcs14/math.hpp"

namespace pcs14 {

// m above where the pressure was `reference_pa`, from the standard atmosphere
float pressure_height(float pressure_pa, float reference_pa);

class HeightFilter {
 public:
  explicit HeightFilter(float crossover = 1.0f) : w_(crossover) {}

  // the vertical acceleration, down positive, from the specific force in the world frame
  void predict(float specific_force_down, float dt);
  // a height measurement (z, down positive), from the barometer or the GPS
  void correct(float z_measured, float dt);
  void reset(float z) {
    z_ = z;
    vz_ = 0;
    bias_ = 0;
  }

  float z() const { return z_; }    // m, down
  float vz() const { return vz_; }  // m/s, down
  float bias() const { return bias_; }

 private:
  float w_;
  float z_ = 0, vz_ = 0, bias_ = 0;
};

}  // namespace pcs14
