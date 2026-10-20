// The mixer: torques and total thrust into each rotor's thrust and speed. GPL-3.0.
//
// Each rotor sits at (x, y) in the body frame (forward-right-down, PX4's CA_ROTOR_PX and _PY)
// and pushes up with thrust T, so it twists the body by (-y T, x T, km T): km is its drag
// torque per thrust, positive for a rotor turning counterclockwise seen from above (PX4's
// CA_ROTOR_KM). The four columns make a 4 x 4 matrix from rotor thrusts to (torque, thrust);
// the mixer inverts it once and multiplies.
//
// When the motors can't give everything, attitude wins over yaw and over climbing: yaw is
// scaled back first, then the whole set shifts up or down to fit, and only then are roll and
// pitch scaled. Each thrust is then a speed by thrust = k w^2, between idle and the top.
#pragma once

#include <array>

#include "pcs14/math.hpp"

namespace pcs14 {

struct Rotor {
  float x, y;  // m from the center of gravity, forward and right
  float km;    // m: drag torque over thrust, + counterclockwise from above
};

struct MixerSetup {
  std::array<Rotor, 4> rotors{};
  float motor_constant = 0;  // N / (rad/s)^2
  float idle_rad_s = 0;
  float max_rad_s = 0;
};

struct Mix {
  std::array<float, 4> thrust{};  // N
  std::array<float, 4> rad_s{};
  bool saturated = false;
};

class Mixer {
 public:
  explicit Mixer(const MixerSetup& setup);

  // torque in N m about the body's axes, thrust in N (up)
  Mix mix(const Vec3& torque, float thrust) const;

  float min_thrust() const { return min_; }
  float max_thrust() const { return max_; }
  // a lower top speed, as a sagging pack gives (never above the motors' own)
  void set_max_rad_s(float max_rad_s);

 private:
  std::array<float, 4> allocate(const Vec3& torque, float thrust) const;
  bool fits(const std::array<float, 4>& t) const;

  MixerSetup setup_;
  float inverse_[4][4]{};  // rotor thrusts from (torque x, y, z, thrust)
  float min_, max_;
};

}  // namespace pcs14
