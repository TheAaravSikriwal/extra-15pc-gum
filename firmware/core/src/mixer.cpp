// The mixer. GPL-3.0.
#include "pcs14/mixer.hpp"

#include <cmath>
#include <utility>

namespace pcs14 {

namespace {
// Gauss-Jordan with partial pivoting; the quad X's matrix is well conditioned
bool invert4(const float in[4][4], float out[4][4]) {
  float m[4][8];
  for (int r = 0; r < 4; ++r)
    for (int c = 0; c < 8; ++c) m[r][c] = c < 4 ? in[r][c] : (c - 4 == r ? 1.0f : 0.0f);
  for (int c = 0; c < 4; ++c) {
    int pivot = c;
    for (int r = c + 1; r < 4; ++r)
      if (std::fabs(m[r][c]) > std::fabs(m[pivot][c])) pivot = r;
    if (std::fabs(m[pivot][c]) < 1e-12f) return false;
    for (int k = 0; k < 8; ++k) std::swap(m[c][k], m[pivot][k]);
    const float p = m[c][c];
    for (int k = 0; k < 8; ++k) m[c][k] /= p;
    for (int r = 0; r < 4; ++r) {
      if (r == c) continue;
      const float f = m[r][c];
      for (int k = 0; k < 8; ++k) m[r][k] -= f * m[c][k];
    }
  }
  for (int r = 0; r < 4; ++r)
    for (int c = 0; c < 4; ++c) out[r][c] = m[r][c + 4];
  return true;
}
}  // namespace

Mixer::Mixer(const MixerSetup& setup) : setup_(setup) {
  float effect[4][4];
  for (int i = 0; i < 4; ++i) {
    const Rotor& r = setup.rotors[i];
    effect[0][i] = -r.y;
    effect[1][i] = r.x;
    effect[2][i] = r.km;
    effect[3][i] = 1.0f;
  }
  invert4(effect, inverse_);
  min_ = setup.motor_constant * setup.idle_rad_s * setup.idle_rad_s;
  max_ = setup.motor_constant * setup.max_rad_s * setup.max_rad_s;
}

void Mixer::set_max_rad_s(float max_rad_s) {
  const float w = clamp(max_rad_s, setup_.idle_rad_s, setup_.max_rad_s);
  max_ = setup_.motor_constant * w * w;
}

std::array<float, 4> Mixer::allocate(const Vec3& torque, float thrust) const {
  const float want[4] = {torque.x, torque.y, torque.z, thrust};
  std::array<float, 4> t{};
  for (int i = 0; i < 4; ++i)
    for (int k = 0; k < 4; ++k) t[i] += inverse_[i][k] * want[k];
  return t;
}

bool Mixer::fits(const std::array<float, 4>& t) const {
  for (float v : t)
    if (v < min_ - 1e-6f || v > max_ + 1e-6f) return false;
  return true;
}

Mix Mixer::mix(const Vec3& torque, float thrust) const {
  Mix out;
  std::array<float, 4> t = allocate(torque, thrust);
  if (!fits(t)) {
    out.saturated = true;
    // 1. give up yaw: the largest share of it that still fits, by bisection
    float lo = 0, hi = 1;
    if (!fits(allocate({torque.x, torque.y, 0}, thrust))) hi = 0;
    for (int k = 0; k < 20 && hi > 0; ++k) {
      const float mid = (lo + hi) / 2;
      (fits(allocate({torque.x, torque.y, torque.z * mid}, thrust)) ? lo : hi) = mid;
    }
    const Vec3 kept{torque.x, torque.y, torque.z * lo};
    t = allocate(kept, thrust);
    if (!fits(t)) {
      // 2. shift the whole set to fit between idle and the top, giving up collective thrust
      float high = t[0], low = t[0];
      for (float v : t) {
        high = std::fmax(high, v);
        low = std::fmin(low, v);
      }
      float shift = 0;
      if (high > max_) shift = max_ - high;
      if (low + shift < min_) shift = min_ - low;
      for (float& v : t) v += shift;
      // 3. still doesn't fit: the spread itself is too wide, so scale the torques down
      if (!fits(t)) {
        const float spread = high - low;
        const float room = max_ - min_;
        const float scale = spread > 0 ? room / spread : 0;
        const float middle = (max_ + min_) / 2;
        const float mean = (high + low) / 2 + shift;
        for (float& v : t) v = middle + (v - mean) * scale;
      }
    }
  }
  for (int i = 0; i < 4; ++i) {
    out.thrust[i] = clamp(t[i], min_, max_);
    out.rad_s[i] = std::sqrt(out.thrust[i] / setup_.motor_constant);
  }
  return out;
}

}  // namespace pcs14
