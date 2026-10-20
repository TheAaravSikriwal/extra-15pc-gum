// The limits. GPL-3.0.
#include "pcs14/limits.hpp"

namespace pcs14 {

void CurrentCap::update(float amps, float dt) {
  const float final = heat_.rise_per_amp2() * amps * amps;
  // exactly the first-order step, so long steps don't overshoot
  rise_ = final + (rise_ - final) * std::exp(-dt / heat_.time_constant());
}

float CurrentCap::allowed(float dt) const {
  const float room = heat_.limit_c - heat_.air_c;
  // the current whose step from here lands on the limit: room = f + (rise - f) e^(-dt/tau)
  const float e = std::exp(-dt / heat_.time_constant());
  const float final = (room - rise_ * e) / (1 - e);
  if (final <= 0) return 0;
  const float amps = std::sqrt(final / heat_.rise_per_amp2());
  return amps < cap_ ? amps : cap_;
}

const LimitsProfile& limits_profile(int index) {
  static const LimitsProfile kProfiles[] = {
      {"max", 0, 0, false},
      {"us-recreational", 121.92f, 0, true},  // 400 ft
  };
  return kProfiles[index == 1 ? 1 : 0];
}

float allowed_height(const LimitsProfile& profile, bool chute) {
  float h = 1e9f;
  if (profile.ceiling_m > 0) h = profile.ceiling_m;
  if (!chute && kParachuteRuleM < h) h = kParachuteRuleM;
  return h;
}

float fence_radius(const LimitsProfile& profile, float own_m) {
  if (own_m <= 0) return profile.fence_m > 0 ? profile.fence_m : 0;
  if (profile.fence_m <= 0) return own_m;
  return own_m < profile.fence_m ? own_m : profile.fence_m;
}

}  // namespace pcs14
