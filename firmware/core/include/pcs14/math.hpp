// Small fixed-size math for the flight code: 3-vectors and unit quaternions. GPL-3.0.
//
// Frames follow PX4's, so its logs and mine read the same: the body is forward-right-down
// (FRD), the world is north-east-down (NED). A quaternion here is (w, x, y, z) and turns body
// vectors into world vectors.
#pragma once

#include <cmath>

namespace pcs14 {

constexpr float kPi = 3.14159265358979f;
constexpr float kG = 9.80665f;  // m/s^2

struct Vec3 {
  float x{0}, y{0}, z{0};

  constexpr Vec3 operator+(const Vec3& o) const { return {x + o.x, y + o.y, z + o.z}; }
  constexpr Vec3 operator-(const Vec3& o) const { return {x - o.x, y - o.y, z - o.z}; }
  constexpr Vec3 operator-() const { return {-x, -y, -z}; }
  constexpr Vec3 operator*(float s) const { return {x * s, y * s, z * s}; }
  constexpr Vec3 operator/(float s) const { return {x / s, y / s, z / s}; }
  Vec3& operator+=(const Vec3& o) { x += o.x; y += o.y; z += o.z; return *this; }
  Vec3& operator-=(const Vec3& o) { x -= o.x; y -= o.y; z -= o.z; return *this; }
  Vec3& operator*=(float s) { x *= s; y *= s; z *= s; return *this; }

  constexpr float dot(const Vec3& o) const { return x * o.x + y * o.y + z * o.z; }
  constexpr Vec3 cross(const Vec3& o) const {
    return {y * o.z - z * o.y, z * o.x - x * o.z, x * o.y - y * o.x};
  }
  float norm() const { return std::sqrt(dot(*this)); }
  Vec3 normalized() const {
    const float n = norm();
    return n > 0 ? *this / n : Vec3{};
  }
};

inline constexpr Vec3 operator*(float s, const Vec3& v) { return v * s; }

struct Quat {
  float w{1}, x{0}, y{0}, z{0};

  static Quat from_axis_angle(const Vec3& axis, float angle) {
    const Vec3 a = axis.normalized() * std::sin(angle / 2);
    return {std::cos(angle / 2), a.x, a.y, a.z};
  }

  // roll about x, then pitch about y, then yaw about z, applied z first (aerospace order)
  static Quat from_euler(float roll, float pitch, float yaw) {
    const float cr = std::cos(roll / 2), sr = std::sin(roll / 2);
    const float cp = std::cos(pitch / 2), sp = std::sin(pitch / 2);
    const float cy = std::cos(yaw / 2), sy = std::sin(yaw / 2);
    return {cr * cp * cy + sr * sp * sy, sr * cp * cy - cr * sp * sy,
            cr * sp * cy + sr * cp * sy, cr * cp * sy - sr * sp * cy};
  }

  constexpr Quat operator*(const Quat& o) const {
    return {w * o.w - x * o.x - y * o.y - z * o.z, w * o.x + x * o.w + y * o.z - z * o.y,
            w * o.y - x * o.z + y * o.w + z * o.x, w * o.z + x * o.y - y * o.x + z * o.w};
  }
  constexpr Quat conjugate() const { return {w, -x, -y, -z}; }
  float norm() const { return std::sqrt(w * w + x * x + y * y + z * z); }
  Quat normalized() const {
    const float n = norm();
    return n > 0 ? Quat{w / n, x / n, y / n, z / n} : Quat{};
  }

  // a body vector in the world frame
  Vec3 rotate(const Vec3& v) const {
    const Quat p{0, v.x, v.y, v.z};
    const Quat r = (*this) * p * conjugate();
    return {r.x, r.y, r.z};
  }
  // a world vector in the body frame
  Vec3 unrotate(const Vec3& v) const { return conjugate().rotate(v); }

  float roll() const { return std::atan2(2 * (w * x + y * z), 1 - 2 * (x * x + y * y)); }
  float pitch() const {
    const float s = 2 * (w * y - z * x);
    return std::asin(s > 1 ? 1 : (s < -1 ? -1 : s));
  }
  float yaw() const { return std::atan2(2 * (w * z + x * y), 1 - 2 * (y * y + z * z)); }
  // rad between the body's down axis and the world's
  float tilt() const {
    const float c = 1 - 2 * (x * x + y * y);
    return std::acos(c > 1 ? 1 : (c < -1 ? -1 : c));
  }
};

// wraps an angle into (-pi, pi]
inline float wrap_pi(float a) {
  while (a > kPi) a -= 2 * kPi;
  while (a <= -kPi) a += 2 * kPi;
  return a;
}

inline float clamp(float v, float lo, float hi) { return v < lo ? lo : (v > hi ? hi : v); }

}  // namespace pcs14
