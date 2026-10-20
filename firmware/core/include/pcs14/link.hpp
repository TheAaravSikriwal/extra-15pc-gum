// The MAVLink link to the ground: what the firmware tells it, and what it asks for. GPL-3.0.
//
// It speaks the way PX4 does, because MAVSDK (which flies the flight sim's scenarios) and
// QGroundControl expect it: a HEARTBEAT with PX4 as the autopilot and PX4's modes, SYS_STATUS
// with the sensors' health bits MAVSDK reads its health from, the telemetry streams at the
// rates MAV_CMD_SET_MESSAGE_INTERVAL asks for, commands answered with COMMAND_ACK, and
// parameters as PX4 encodes them (an int32's bytes carried in the float field). The notes on
// what MAVSDK needs are in docs/plans/2026-10-20-firmware.md.
//
// Like the ULog writer it doesn't touch any port: bytes come in through receive() and go out
// through a sink, so the same code runs over UDP in the sim and over a radio on the drone.
#pragma once

#include <cstdint>
#include <functional>
#include <memory>

#include "pcs14/math.hpp"
#include "pcs14/modes.hpp"
#include "pcs14/params.hpp"

namespace pcs14 {

// MAVLink's MAV_LANDED_STATE
enum class Landed : uint8_t { Unknown = 0, OnGround = 1, InAir = 2, TakingOff = 3, Landing = 4 };

// what the firmware knows, for the streams
struct Telemetry {
  uint64_t t_us = 0;  // since boot
  bool armed = false;
  Mode mode = Mode::Manual;
  Quat attitude;  // body (forward-right-down) to north-east-down
  Vec3 rates;     // rad/s, body
  Vec3 gyro, accel;  // rad/s, m/s^2 (specific force), body
  Vec3 mag;          // gauss, body
  float pressure_hpa = 1013.25f, temperature_c = 20;
  bool position_valid = false;  // the local position estimate
  Vec3 position, velocity;      // m, m/s, north-east-down from the origin
  bool global_valid = false;    // the global position (from the GPS until the estimator has it)
  double lat_deg = 0, lon_deg = 0;
  float alt_msl_m = 0, alt_rel_m = 0;
  bool home_valid = false;
  double home_lat_deg = 0, home_lon_deg = 0;
  float home_alt_msl_m = 0;
  Vec3 home_position;  // m, north-east-down from the origin
  Landed landed = Landed::OnGround;
  bool gps_fix = false;
  uint8_t satellites = 0;
  float battery_v = 0, battery_a = 0;
  float battery_remaining = -1;  // 0 to 1, or -1 when unknown
  bool armable = false;          // the pre-arm checks pass
};

// something the ground asked for
struct Request {
  enum class Kind : uint8_t {
    Arm, Disarm, ForceDisarm, Takeoff, Land, Return, SetMode, Terminate, InjectFailure
  };
  Kind kind;
  Mode mode = Mode::Manual;  // for SetMode
  uint8_t failure_unit = 0, failure_type = 0, failure_instance = 0;  // MAVLink's FAILURE_UNIT
                                                                     // and FAILURE_TYPE
};

// SET_POSITION_TARGET_LOCAL_NED, as offboard control sends it
struct OffboardSetpoint {
  uint64_t t_us;
  uint16_t ignore;  // MAVLink's POSITION_TARGET_TYPEMASK: the bits of the fields to ignore
  Vec3 position, velocity, accel;  // north-east-down
  float yaw, yaw_rate;
};

// MANUAL_CONTROL: x pitch (forward +), y roll (right +), z throttle, r yaw, as -1 to 1 (z 0 to
// 1)
struct ManualInput {
  uint64_t t_us;
  float x, y, z, r;
};

class Link {
 public:
  using Send = std::function<void(const uint8_t* data, size_t size)>;
  struct Handlers {
    std::function<bool(const Request&)> request;  // true when the vehicle takes it
    std::function<void(const OffboardSetpoint&)> offboard;
    std::function<void(const ManualInput&)> manual;
  };

  Link(Params& params, Send send, Handlers handlers, uint8_t system = 1, uint8_t component = 1);
  ~Link();

  // bytes from the ground, at `now_us` since boot
  void receive(const uint8_t* data, size_t size, uint64_t now_us);
  // sends whatever stream is due, from the latest telemetry
  void update(const Telemetry& t);
  // a line for the ground station to show, at MAVLink's MAV_SEVERITY (6 info, 4 warning)
  void status_text(uint8_t severity, const char* text);
  // when the ground station's last heartbeat came in, or 0 if none ever has
  uint64_t last_ground_heartbeat_us() const;

 private:
  struct Impl;
  std::unique_ptr<Impl> impl_;
};

}  // namespace pcs14
