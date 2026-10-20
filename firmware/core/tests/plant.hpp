// A small rigid-body quad for the host tests: the drone the flight loop flies when there's no
// Gazebo. Frames as in the firmware: world north-east-down, body forward-right-down.
//
// Each motor chases its commanded speed with a first-order lag (faster up than down, like the
// sim's motor model), each rotor pushes k w^2 along the body's -z and twists the body by its
// drag torque, gravity pulls, and the ground stops the fall. Integrated in 1 ms steps.
#pragma once

#include <array>
#include <cmath>

#include "pcs14/flight.hpp"

namespace pcs14::test {

struct Plant {
  Airframe frame;
  Vec3 position, velocity;  // m, m/s, NED; z is negative above the ground
  Quat q;                   // body to world
  Vec3 rate;                // rad/s, body
  std::array<float, 4> speed{};  // rad/s, each motor
  Vec3 cg_offset;           // m: where the weight really sits, against where the frame says
  Vec3 push;                // N, world: a steady outside force, like wind
  float drag_area = 0.012f;         // m^2, base's, like the flight sim's drag plugin
  float rotor_drag = 8.06428e-05f;  // N per (rad/s) per (m/s), each rotor, Gazebo's model's
  float tau_up = 0.0125f, tau_down = 0.025f;  // s

  explicit Plant(const Airframe& f) : frame(f) {}

  bool on_ground() const { return position.z >= 0 && velocity.z >= 0; }

  // the accelerometer: the specific force in the body frame, what the IMU feels
  Vec3 accel() const { return q.unrotate(specific_force_world()); }

  // the barometer, Pa: the standard atmosphere at the drone's height, from 101325 at the ground
  float pressure() const {
    return 101325.0f * std::pow(1.0f - (-position.z) / 44330.0f, 1.0f / 0.190295f);
  }

  void step(const std::array<float, 4>& command, float dt) {
    constexpr float h = 0.001f;
    for (float t = 0; t < dt - 1e-6f; t += h) substep(command, h);
  }

 private:
  Vec3 thrust_body() const {
    float total = 0;
    for (float w : speed) total += frame.mixer.motor_constant * w * w;
    return {0, 0, -total};
  }
  // the air's push: body drag on the speed squared, and the rotors' drag across their discs
  Vec3 drag_world() const {
    const float v = velocity.norm();
    Vec3 f = velocity * (-0.5f * 1.225f * drag_area * v);
    float spin = 0;
    for (float w : speed) spin += w;
    const Vec3 body = q.unrotate(velocity);
    f += q.rotate(Vec3{body.x, body.y, 0} * (-rotor_drag * spin));
    return f;
  }
  Vec3 specific_force_world() const {
    const Vec3 f = q.rotate(thrust_body()) + push + drag_world();
    // resting on the ground, the ground carries what the rotors don't: the IMU feels 1 g up
    if (on_ground() && f.z + frame.mass_kg * kG >= 0) return {0, 0, -kG};
    return f / frame.mass_kg;
  }
  void substep(const std::array<float, 4>& command, float h) {
    Vec3 torque;
    for (size_t i = 0; i < 4; ++i) {
      const float tau = command[i] > speed[i] ? tau_up : tau_down;
      speed[i] += (command[i] - speed[i]) * h / tau;
      const Rotor& r = frame.mixer.rotors[i];
      const float t = frame.mixer.motor_constant * speed[i] * speed[i];
      // the rotor sits at (x, y) from where the frame thinks the weight is; the weight is
      // really cg_offset further along
      const float x = r.x - cg_offset.x, y = r.y - cg_offset.y;
      torque += Vec3{-y * t, x * t, r.km * t};
    }
    const Vec3& j = frame.inertia;
    const Vec3 jw{j.x * rate.x, j.y * rate.y, j.z * rate.z};
    const Vec3 net = torque - rate.cross(jw);
    const Vec3 world_force =
        q.rotate(thrust_body()) + push + drag_world() + Vec3{0, 0, frame.mass_kg * kG};
    if (on_ground() && world_force.z >= 0) {
      // resting: the ground holds it level and still
      velocity = {};
      rate = {};
      position.z = 0;
      return;
    }
    rate += Vec3{net.x / j.x, net.y / j.y, net.z / j.z} * h;
    velocity += world_force / frame.mass_kg * h;
    position += velocity * h;
    const Quat dq{0, rate.x * 0.5f * h, rate.y * 0.5f * h, rate.z * 0.5f * h};
    const Quat s = q * dq;
    q = Quat{q.w + s.w, q.x + s.x, q.y + s.y, q.z + s.z}.normalized();
  }
};

// the base combination's numbers, from the flight sim's model (2026-10-20)
inline Airframe base_airframe() {
  Airframe a;
  a.mass_kg = 1.86f;
  a.inertia = {0.0125f, 0.0155f, 0.0233f};
  constexpr float x = 0.1485f;
  a.mixer.rotors = {{{x, x, 0.016f}, {-x, -x, 0.016f}, {x, -x, -0.016f}, {-x, x, -0.016f}}};
  a.mixer.motor_constant = 1.5777e-5f;
  a.mixer.idle_rad_s = 142.0f;
  a.mixer.max_rad_s = 947.0f;
  return a;
}

}  // namespace pcs14::test
