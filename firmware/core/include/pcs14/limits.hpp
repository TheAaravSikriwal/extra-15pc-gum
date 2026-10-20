// The limits: the current cap with the XT60's heat limit, the limits profile, and the
// parachute rule. GPL-3.0.
//
// The current cap (step 1, then step 3d): the battery current is capped at 90 A, the pack's
// continuous rating, and eased below that to keep the XT60 under its limit. The XT60 heats
// like pcs14.electrical.thermal's ConnectorModel: its steady rise goes with the current squared
// (Amass: 85 K at 35 A), approached with a time constant from its contact's resistance and heat
// capacity. Each step the cap is the most current that keeps the next step's rise inside the
// limit, so it holds 90 A while the contact is cool and settles at the 29 A the XT60 carries
// forever once it's hot.
//
// The limits profile ("government rules are settings, not caps", decided 2026-10-14): the
// legal numbers live in a profile, switched from the ground station, and the active one goes
// into every log. Two to start: us-recreational (the FAA's 400 ft ceiling) and max (only what
// the hardware can do).
//
// The parachute rule, my own rule, not the government's: no autonomous flight above about
// 30 m without P (the chute).
#pragma once

#include <cmath>
#include <cstdint>

#include "pcs14/math.hpp"

namespace pcs14 {

// the connector's heat model, with design/catalog's Amass XT60 numbers and the electrical
// step's thermal settings (design/electrical.yaml)
struct ConnectorHeat {
  float rated_a = 35.0f;    // Amass: 35 A...
  float rise_c = 85.0f;     // ...for an 85 K rise
  float contact_ohms = 0.001f;
  float heat_capacity = 1.407f;  // J/K: 2.5 g of brass plus 2 cm of 12 AWG copper each side
  float limit_c = 100.0f;   // its 120 C rating less the 20 C margin
  float air_c = 40.0f;      // a hot day, inside the frame
  float rise_per_amp2() const { return rise_c / (rated_a * rated_a); }
  float time_constant() const { return rise_per_amp2() / contact_ohms * heat_capacity; }
  float holds() const { return rated_a * std::sqrt((limit_c - air_c) / rise_c); }
};

class CurrentCap {
 public:
  explicit CurrentCap(float cap_a = 90.0f, const ConnectorHeat& heat = {}, float start_rise = 0)
      : cap_(cap_a), heat_(heat), rise_(start_rise) {}

  // the battery current this step (A) and how long it lasted
  void update(float amps, float dt);
  // the most current allowed for the next `dt`
  float allowed(float dt) const;
  float rise() const { return rise_; }  // K over the air
  float temperature() const { return heat_.air_c + rise_; }

 private:
  float cap_;
  ConnectorHeat heat_;
  float rise_;
};

struct LimitsProfile {
  const char* name;
  float ceiling_m;      // over home; 0 is none
  float fence_m;        // from home; 0 is none
  bool remote_id;       // expected fitted (the firmware never refuses to arm without it)
};
// 0: max, 1: us-recreational, by the parameter PCS14_LIMITS
const LimitsProfile& limits_profile(int index);

constexpr float kParachuteRuleM = 30.0f;  // without the chute, no autonomous flight above this

// the height (m over home) an autonomous setpoint may ask for, under the profile's ceiling and,
// without the chute, the parachute rule
float allowed_height(const LimitsProfile& profile, bool chute);

// the geofence's radius (m from home): the tighter of the day's own (GF_MAX_HOR_DIST) and the
// profile's, either one 0 for none; 0 when neither has one
float fence_radius(const LimitsProfile& profile, float own_m);

}  // namespace pcs14
