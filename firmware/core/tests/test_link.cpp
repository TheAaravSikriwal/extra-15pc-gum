// The MAVLink link and the parameters, against a ground station made of the same MAVLink
// library, behaving the way MAVSDK does.
#include <doctest/doctest.h>

#include <common/mavlink.h>

#include <cstring>
#include <vector>

#include "pcs14/link.hpp"
#include "pcs14/params.hpp"

using namespace pcs14;

namespace {
constexpr uint8_t kGround = 245;  // MAVSDK's own system id

struct Ground {
  std::vector<mavlink_message_t> heard;
  mavlink_message_t buffer{};
  mavlink_status_t status{};

  // what the vehicle sent, parsed
  Link::Send ear() {
    return [this](const uint8_t* d, size_t n) {
      for (size_t k = 0; k < n; ++k) {
        mavlink_message_t msg;
        mavlink_status_t s;
        if (mavlink_frame_char_buffer(&buffer, &status, d[k], &msg, &s) == MAVLINK_FRAMING_OK)
          heard.push_back(msg);
      }
    };
  }
  // sends a message to the vehicle
  static void say(Link& link, const mavlink_message_t& msg, uint64_t now_us = 1000) {
    uint8_t bytes[MAVLINK_MAX_PACKET_LEN];
    const uint16_t n = mavlink_msg_to_send_buffer(bytes, &msg);
    link.receive(bytes, n, now_us);
  }
  static mavlink_message_t command(uint16_t id, float p1 = 0, float p2 = 0, float p3 = 0) {
    mavlink_command_long_t c{};
    c.command = id;
    c.target_system = 1;
    c.target_component = 1;
    c.param1 = p1;
    c.param2 = p2;
    c.param3 = p3;
    mavlink_message_t msg;
    mavlink_msg_command_long_encode(kGround, MAV_COMP_ID_MISSIONPLANNER, &msg, &c);
    return msg;
  }
  std::vector<mavlink_message_t> of(uint32_t id) const {
    std::vector<mavlink_message_t> out;
    for (const auto& m : heard)
      if (m.msgid == id) out.push_back(m);
    return out;
  }
  uint8_t last_ack(uint16_t command) const {
    for (auto it = heard.rbegin(); it != heard.rend(); ++it) {
      if (it->msgid != MAVLINK_MSG_ID_COMMAND_ACK) continue;
      mavlink_command_ack_t a;
      mavlink_msg_command_ack_decode(&*it, &a);
      if (a.command == command) return a.result;
    }
    return 255;
  }
};

struct Vehicle {
  std::vector<Request> asked;
  bool accept = true;
  std::vector<ManualInput> sticks;
  Link::Handlers handlers() {
    Link::Handlers h;
    h.request = [this](const Request& r) {
      asked.push_back(r);
      return accept;
    };
    h.manual = [this](const ManualInput& m) { sticks.push_back(m); };
    return h;
  }
};
}  // namespace

TEST_CASE("parameters keep their type and take new names") {
  Params p;
  p.add("MC_ROLL_P", 9.0f);
  p.add_int("COM_RC_IN_MODE", 0);
  p.add("MC_ROLL_P", 1.0f);  // declaring again keeps the value
  CHECK(p.get("MC_ROLL_P") == doctest::Approx(9.0f));
  p.set_int("COM_RC_IN_MODE", 1);
  CHECK(p.get_int("COM_RC_IN_MODE") == 1);
  const size_t index = p.set("MIS_TAKEOFF_ALT", 10.0f);  // a name the code didn't declare
  CHECK(p.at(index).name == "MIS_TAKEOFF_ALT");
  CHECK(p.get("NO_SUCH_PARAM", 3.0f) == doctest::Approx(3.0f));
}

TEST_CASE("the heartbeat says PX4, a quadrotor, armed or not, and PX4's mode") {
  Params params;
  Ground ground;
  Vehicle vehicle;
  Link link(params, ground.ear(), vehicle.handlers());
  Telemetry t;
  t.t_us = 1000000;
  t.mode = Mode::Hold;
  t.armed = true;
  link.update(t);
  const auto beats = ground.of(MAVLINK_MSG_ID_HEARTBEAT);
  REQUIRE(beats.size() == 1);
  mavlink_heartbeat_t h;
  mavlink_msg_heartbeat_decode(&beats[0], &h);
  CHECK(h.autopilot == MAV_AUTOPILOT_PX4);
  CHECK(h.type == MAV_TYPE_QUADROTOR);
  CHECK((h.base_mode & MAV_MODE_FLAG_SAFETY_ARMED) != 0);
  CHECK((h.base_mode & MAV_MODE_FLAG_CUSTOM_MODE_ENABLED) != 0);
  CHECK(h.custom_mode == px4_custom_mode(Mode::Hold));
  CHECK(beats[0].sysid == 1);
}

TEST_CASE("streams go out at their rates, and SET_MESSAGE_INTERVAL changes them") {
  Params params;
  Ground ground;
  Vehicle vehicle;
  Link link(params, ground.ear(), vehicle.handlers());
  Ground::say(link, Ground::command(MAV_CMD_SET_MESSAGE_INTERVAL, MAVLINK_MSG_ID_HIGHRES_IMU,
                                    20000));  // 50 Hz
  CHECK(ground.last_ack(MAV_CMD_SET_MESSAGE_INTERVAL) == MAV_RESULT_ACCEPTED);
  Telemetry t;
  for (int k = 0; k < 1000; ++k) {  // one second at 1 kHz
    t.t_us = 1000000 + static_cast<uint64_t>(k) * 1000;
    link.update(t);
  }
  CHECK(ground.of(MAVLINK_MSG_ID_HIGHRES_IMU).size() == 50);
  CHECK(ground.of(MAVLINK_MSG_ID_HEARTBEAT).size() == 1);
  CHECK(ground.of(MAVLINK_MSG_ID_ATTITUDE_QUATERNION).size() == 10);
  // no position estimate yet: no LOCAL_POSITION_NED
  CHECK(ground.of(MAVLINK_MSG_ID_LOCAL_POSITION_NED).empty());
}

TEST_CASE("SYS_STATUS reports the GPS healthy only with a fix and a position") {
  Params params;
  Ground ground;
  Vehicle vehicle;
  Link link(params, ground.ear(), vehicle.handlers());
  Telemetry t;
  t.t_us = 1000000;
  link.update(t);
  t.t_us = 2000000;
  t.gps_fix = t.global_valid = t.armable = true;
  link.update(t);
  const auto status = ground.of(MAVLINK_MSG_ID_SYS_STATUS);
  REQUIRE(status.size() == 2);
  mavlink_sys_status_t before, after;
  mavlink_msg_sys_status_decode(&status[0], &before);
  mavlink_msg_sys_status_decode(&status[1], &after);
  CHECK((before.onboard_control_sensors_present & MAV_SYS_STATUS_SENSOR_GPS) != 0);
  CHECK((before.onboard_control_sensors_health & MAV_SYS_STATUS_SENSOR_GPS) == 0);
  CHECK((after.onboard_control_sensors_health & MAV_SYS_STATUS_SENSOR_GPS) != 0);
  CHECK((after.onboard_control_sensors_health & MAV_SYS_STATUS_PREARM_CHECK) != 0);
}

TEST_CASE("commands go to the vehicle and come back acknowledged") {
  Params params;
  Ground ground;
  Vehicle vehicle;
  Link link(params, ground.ear(), vehicle.handlers());
  Ground::say(link, Ground::command(MAV_CMD_COMPONENT_ARM_DISARM, 1));
  CHECK(ground.last_ack(MAV_CMD_COMPONENT_ARM_DISARM) == MAV_RESULT_ACCEPTED);
  REQUIRE(vehicle.asked.size() == 1);
  CHECK(vehicle.asked[0].kind == Request::Kind::Arm);

  // MAVSDK's hold: DO_SET_MODE with PX4's auto main mode and the loiter sub mode
  Ground::say(link, Ground::command(MAV_CMD_DO_SET_MODE, MAV_MODE_FLAG_CUSTOM_MODE_ENABLED,
                                    px4::kAuto, px4::kAutoLoiter));
  CHECK(vehicle.asked.back().kind == Request::Kind::SetMode);
  CHECK(vehicle.asked.back().mode == Mode::Hold);

  vehicle.accept = false;
  Ground::say(link, Ground::command(MAV_CMD_NAV_TAKEOFF));
  CHECK(ground.last_ack(MAV_CMD_NAV_TAKEOFF) == MAV_RESULT_DENIED);

  Ground::say(link, Ground::command(MAV_CMD_DO_REPOSITION));  // not flown (yet)
  CHECK(ground.last_ack(MAV_CMD_DO_REPOSITION) == MAV_RESULT_UNSUPPORTED);

  // failure injection needs SYS_FAILURE_EN, as in PX4
  vehicle.accept = true;
  Ground::say(link, Ground::command(MAV_CMD_INJECT_FAILURE, FAILURE_UNIT_SYSTEM_MOTOR,
                                    FAILURE_TYPE_OFF, 1));
  CHECK(ground.last_ack(MAV_CMD_INJECT_FAILURE) == MAV_RESULT_DENIED);
  params.set_int("SYS_FAILURE_EN", 1);
  Ground::say(link, Ground::command(MAV_CMD_INJECT_FAILURE, FAILURE_UNIT_SYSTEM_MOTOR,
                                    FAILURE_TYPE_OFF, 1));
  CHECK(ground.last_ack(MAV_CMD_INJECT_FAILURE) == MAV_RESULT_ACCEPTED);
  CHECK(vehicle.asked.back().failure_unit == FAILURE_UNIT_SYSTEM_MOTOR);
  CHECK(vehicle.asked.back().failure_instance == 1);
}

TEST_CASE("a parameter set is echoed back, an int32 carried bytewise as PX4 does") {
  Params params;
  params.add_int("COM_RC_IN_MODE", 0);
  Ground ground;
  Vehicle vehicle;
  Link link(params, ground.ear(), vehicle.handlers());

  mavlink_param_set_t set{};
  set.target_system = 1;
  std::strncpy(set.param_id, "COM_RC_IN_MODE", sizeof(set.param_id));
  const int32_t one = 1;
  float raw;
  std::memcpy(&raw, &one, sizeof(raw));
  set.param_value = raw;
  set.param_type = MAV_PARAM_TYPE_INT32;
  mavlink_message_t msg;
  mavlink_msg_param_set_encode(kGround, MAV_COMP_ID_MISSIONPLANNER, &msg, &set);
  Ground::say(link, msg);
  CHECK(params.get_int("COM_RC_IN_MODE") == 1);

  std::strncpy(set.param_id, "MIS_TAKEOFF_ALT", sizeof(set.param_id));
  set.param_value = 10.0f;
  set.param_type = MAV_PARAM_TYPE_REAL32;
  mavlink_msg_param_set_encode(kGround, MAV_COMP_ID_MISSIONPLANNER, &msg, &set);
  Ground::say(link, msg);
  CHECK(params.get("MIS_TAKEOFF_ALT") == doctest::Approx(10.0f));

  const auto values = ground.of(MAVLINK_MSG_ID_PARAM_VALUE);
  REQUIRE(values.size() == 2);
  mavlink_param_value_t v;
  mavlink_msg_param_value_decode(&values[0], &v);
  int32_t carried;
  const float echoed = v.param_value;
  std::memcpy(&carried, &echoed, sizeof(carried));
  CHECK(carried == 1);
  CHECK(v.param_type == MAV_PARAM_TYPE_INT32);
  mavlink_msg_param_value_decode(&values[1], &v);
  CHECK(std::string(v.param_id, strnlen(v.param_id, 16)) == "MIS_TAKEOFF_ALT");
  CHECK(v.param_count == 2);
}

TEST_CASE("the ground's heartbeat is timed, and its sticks come through scaled") {
  Params params;
  Ground ground;
  Vehicle vehicle;
  Link link(params, ground.ear(), vehicle.handlers());
  CHECK(link.last_ground_heartbeat_us() == 0);
  mavlink_heartbeat_t h{};
  h.type = MAV_TYPE_GCS;
  h.autopilot = MAV_AUTOPILOT_INVALID;
  mavlink_message_t msg;
  mavlink_msg_heartbeat_encode(kGround, MAV_COMP_ID_MISSIONPLANNER, &msg, &h);
  Ground::say(link, msg, 5000000);
  CHECK(link.last_ground_heartbeat_us() == 5000000);

  mavlink_manual_control_t m{};
  m.target = 1;
  m.x = 500;
  m.y = -250;
  m.z = 600;
  m.r = 0;
  mavlink_msg_manual_control_encode(kGround, MAV_COMP_ID_MISSIONPLANNER, &msg, &m);
  Ground::say(link, msg);
  REQUIRE(vehicle.sticks.size() == 1);
  CHECK(vehicle.sticks[0].x == doctest::Approx(0.5f));
  CHECK(vehicle.sticks[0].y == doctest::Approx(-0.25f));
  CHECK(vehicle.sticks[0].z == doctest::Approx(0.6f));
}

TEST_CASE("asked for, AUTOPILOT_VERSION says it encodes parameters bytewise") {
  Params params;
  Ground ground;
  Vehicle vehicle;
  Link link(params, ground.ear(), vehicle.handlers());
  Ground::say(link, Ground::command(MAV_CMD_REQUEST_MESSAGE, MAVLINK_MSG_ID_AUTOPILOT_VERSION));
  Telemetry t;
  t.t_us = 1000;
  link.update(t);
  const auto v = ground.of(MAVLINK_MSG_ID_AUTOPILOT_VERSION);
  REQUIRE(v.size() == 1);
  mavlink_autopilot_version_t a;
  mavlink_msg_autopilot_version_decode(&v[0], &a);
  CHECK((a.capabilities & MAV_PROTOCOL_CAPABILITY_PARAM_ENCODE_BYTEWISE) != 0);
  CHECK((a.capabilities & MAV_PROTOCOL_CAPABILITY_MAVLINK2) != 0);
}
