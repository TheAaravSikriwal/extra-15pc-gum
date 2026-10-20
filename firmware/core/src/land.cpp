// The land detector. GPL-3.0.
#include "pcs14/land.hpp"

#include <cmath>

namespace pcs14 {

namespace {
constexpr float kLowThrust = 0.6f;     // of the weight: well under a hover
constexpr float kHoverThrust = 0.9f;   // of the weight: near a hover
constexpr float kStill = 0.3f;         // m/s
constexpr float kQuietFor = 1.0f;      // s
constexpr float kOffTheGround = 0.3f;  // m
}  // namespace

void LandDetector::update(bool armed, float thrust_share, float vz, float height, float dt) {
  if (!armed) {
    landed_ = true;
    quiet_ = 0;
    landed_for_ += dt;
    return;
  }
  if (landed_) {
    if (thrust_share > kHoverThrust && (vz < -kStill || height > kOffTheGround)) {
      landed_ = false;
      landed_for_ = 0;
    } else {
      landed_for_ += dt;
    }
    return;
  }
  const bool quiet = thrust_share < kLowThrust && std::fabs(vz) < kStill;
  quiet_ = quiet ? quiet_ + dt : 0;
  if (quiet_ >= kQuietFor) {
    landed_ = true;
    landed_for_ = 0;
    quiet_ = 0;
  }
}

}  // namespace pcs14
