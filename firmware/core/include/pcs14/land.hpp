// The land detector: is the drone on the ground? GPL-3.0.
//
// On the ground the motors carry less than the weight and nothing moves; in the air they carry
// about all of it. So: landed after the thrust has sat well under the hover thrust with the
// vertical speed near zero for a second, and in the air once the thrust is near the hover
// thrust and it's climbing or off the ground. Disarmed is always landed. PX4's works the same
// way with more cases (MC_LandDetector), and like PX4 it's what arms the auto-disarm.
#pragma once

namespace pcs14 {

class LandDetector {
 public:
  // the thrust as a share of the weight, the vertical speed (m/s, down positive) and the
  // height above where it took off (m, up)
  void update(bool armed, float thrust_share, float vz, float height, float dt);
  bool landed() const { return landed_; }
  float landed_for() const { return landed_for_; }  // s

 private:
  bool landed_ = true;
  float quiet_ = 0, landed_for_ = 0;
};

}  // namespace pcs14
