// The MAVLink link. GPL-3.0.
#include "pcs14/link.hpp"

#include <common/mavlink.h>

#include <algorithm>
#include <cmath>
#include <cstring>
#include <map>

namespace pcs14 {

namespace {
constexpr uint8_t kAutopilotPx4 = MAV_AUTOPILOT_PX4;
constexpr float kForceDisarm = 21196.0f;  // MAV_CMD_COMPONENT_ARM_DISARM's magic for "now"
constexpr uint64_t kDefault = 0;          // a stream at its default rate

// the streams, by message id, and their default intervals in us (0: only when asked)
const std::map<uint32_t, uint64_t> kDefaults = {
    {MAVLINK_MSG_ID_HEARTBEAT, 1000000},
    {MAVLINK_MSG_ID_SYS_STATUS, 1000000},
    {MAVLINK_MSG_ID_EXTENDED_SYS_STATE, 1000000},
    {MAVLINK_MSG_ID_ATTITUDE_QUATERNION, 100000},
    {MAVLINK_MSG_ID_HIGHRES_IMU, 0},
    {MAVLINK_MSG_ID_LOCAL_POSITION_NED, 100000},
    {MAVLINK_MSG_ID_GLOBAL_POSITION_INT, 100000},
    {MAVLINK_MSG_ID_GPS_RAW_INT, 1000000},
    {MAVLINK_MSG_ID_HOME_POSITION, 2000000},
    {MAVLINK_MSG_ID_BATTERY_STATUS, 1000000},
};

uint32_t sensors_present() {
  return MAV_SYS_STATUS_SENSOR_3D_GYRO | MAV_SYS_STATUS_SENSOR_3D_ACCEL |
         MAV_SYS_STATUS_SENSOR_3D_MAG | MAV_SYS_STATUS_SENSOR_ABSOLUTE_PRESSURE |
         MAV_SYS_STATUS_SENSOR_GPS | MAV_SYS_STATUS_SENSOR_MOTOR_OUTPUTS |
         MAV_SYS_STATUS_AHRS | MAV_SYS_STATUS_PREARM_CHECK;
}

std::string param_name(const char* id) {
  char name[17] = {};
  std::memcpy(name, id, 16);
  return name;
}
}  // namespace

struct Link::Impl {
  Params& params;
  Send send;
  Handlers handlers;
  uint8_t system, component;
  mavlink_message_t rx_buffer{};
  mavlink_status_t rx_status{};
  uint64_t ground_heartbeat_us = 0;
  uint8_t ground_system = 255, ground_component = MAV_COMP_ID_MISSIONPLANNER;
  struct Stream {
    uint64_t interval_us;
    uint64_t next_us = 0;
  };
  std::map<uint32_t, Stream> streams;
  std::vector<uint32_t> once;  // messages asked for with MAV_CMD_REQUEST_MESSAGE
  bool send_all_params = false;
  size_t next_param = 0;

  Impl(Params& p, Send s, Handlers h, uint8_t sys, uint8_t comp)
      : params(p), send(std::move(s)), handlers(std::move(h)), system(sys), component(comp) {
    for (const auto& [id, us] : kDefaults) streams[id] = {us};
  }

  void out(const mavlink_message_t& msg) {
    uint8_t buffer[MAVLINK_MAX_PACKET_LEN];
    const uint16_t n = mavlink_msg_to_send_buffer(buffer, &msg);
    send(buffer, n);
  }

  void ack(uint16_t command, uint8_t result) {
    mavlink_command_ack_t a{};
    a.command = command;
    a.result = result;
    a.target_system = ground_system;
    a.target_component = ground_component;
    mavlink_message_t msg;
    mavlink_msg_command_ack_encode(system, component, &msg, &a);
    out(msg);
  }

  void param_value(size_t index) {
    const Params::Param& p = params.at(index);
    mavlink_param_value_t v{};
    // MAVLink's names fill all 16 bytes without a terminator when they're that long
    std::memcpy(v.param_id, p.name.data(), std::min(p.name.size(), sizeof(v.param_id)));
    if (p.type == Params::Type::Float) {
      v.param_type = MAV_PARAM_TYPE_REAL32;
      v.param_value = p.f;
    } else {
      v.param_type = MAV_PARAM_TYPE_INT32;
      float raw;  // PX4's bytewise encoding: the int32's bytes in the float
      std::memcpy(&raw, &p.i, sizeof(raw));
      v.param_value = raw;
    }
    v.param_count = static_cast<uint16_t>(params.size());
    v.param_index = static_cast<uint16_t>(index);
    mavlink_message_t msg;
    mavlink_msg_param_value_encode(system, component, &msg, &v);
    out(msg);
  }

  bool ask(const Request& r) { return handlers.request ? handlers.request(r) : false; }

  uint8_t command(uint16_t id, float p1, float p2, float p3) {
    using K = Request::Kind;
    switch (id) {
      case MAV_CMD_COMPONENT_ARM_DISARM: {
        const K kind = p1 > 0.5f ? K::Arm : (p2 == kForceDisarm ? K::ForceDisarm : K::Disarm);
        return ask({kind}) ? MAV_RESULT_ACCEPTED : MAV_RESULT_DENIED;
      }
      case MAV_CMD_NAV_TAKEOFF:
        return ask({K::Takeoff}) ? MAV_RESULT_ACCEPTED : MAV_RESULT_DENIED;
      case MAV_CMD_NAV_LAND:
        return ask({K::Land}) ? MAV_RESULT_ACCEPTED : MAV_RESULT_DENIED;
      case MAV_CMD_NAV_RETURN_TO_LAUNCH:
        return ask({K::Return}) ? MAV_RESULT_ACCEPTED : MAV_RESULT_DENIED;
      case MAV_CMD_DO_FLIGHTTERMINATION:
        if (p1 < 0.5f) return MAV_RESULT_ACCEPTED;  // "don't terminate" is always fine
        return ask({K::Terminate}) ? MAV_RESULT_ACCEPTED : MAV_RESULT_DENIED;
      case MAV_CMD_DO_SET_MODE: {
        Request r{K::SetMode};
        if (!mode_from_px4(static_cast<uint8_t>(p2), static_cast<uint8_t>(p3), r.mode))
          return MAV_RESULT_UNSUPPORTED;
        return ask(r) ? MAV_RESULT_ACCEPTED : MAV_RESULT_DENIED;
      }
      case MAV_CMD_INJECT_FAILURE: {
        if (params.get_int("SYS_FAILURE_EN", 0) != 1) return MAV_RESULT_DENIED;  // as PX4
        Request r{K::InjectFailure};
        r.failure_unit = static_cast<uint8_t>(p1);
        r.failure_type = static_cast<uint8_t>(p2);
        r.failure_instance = static_cast<uint8_t>(p3);
        return ask(r) ? MAV_RESULT_ACCEPTED : MAV_RESULT_UNSUPPORTED;
      }
      case MAV_CMD_SET_MESSAGE_INTERVAL: {
        const auto msg_id = static_cast<uint32_t>(p1);
        auto found = streams.find(msg_id);
        if (found == streams.end()) return MAV_RESULT_UNSUPPORTED;
        if (p2 < 0) found->second.interval_us = 0;  // off
        else if (p2 == 0) found->second.interval_us = kDefaults.at(msg_id);
        else found->second.interval_us = static_cast<uint64_t>(p2);
        found->second.next_us = 0;
        return MAV_RESULT_ACCEPTED;
      }
      case MAV_CMD_REQUEST_MESSAGE:
        once.push_back(static_cast<uint32_t>(p1));
        return MAV_RESULT_ACCEPTED;
      case MAV_CMD_REQUEST_AUTOPILOT_CAPABILITIES:
        once.push_back(MAVLINK_MSG_ID_AUTOPILOT_VERSION);
        return MAV_RESULT_ACCEPTED;
      default:
        (void)kDefault;
        return MAV_RESULT_UNSUPPORTED;
    }
  }

  void handle(const mavlink_message_t& msg, uint64_t now_us) {
    switch (msg.msgid) {
      case MAVLINK_MSG_ID_HEARTBEAT: {
        mavlink_heartbeat_t h;
        mavlink_msg_heartbeat_decode(&msg, &h);
        if (h.type == MAV_TYPE_GCS) {
          ground_heartbeat_us = now_us;
          ground_system = static_cast<uint8_t>(msg.sysid);
          ground_component = msg.compid;
        }
        break;
      }
      case MAVLINK_MSG_ID_COMMAND_LONG: {
        mavlink_command_long_t c;
        mavlink_msg_command_long_decode(&msg, &c);
        if (c.target_system != 0 && c.target_system != system) break;
        ground_system = static_cast<uint8_t>(msg.sysid);
        ground_component = msg.compid;
        ack(c.command, command(c.command, c.param1, c.param2, c.param3));
        break;
      }
      case MAVLINK_MSG_ID_COMMAND_INT: {
        mavlink_command_int_t c;
        mavlink_msg_command_int_decode(&msg, &c);
        if (c.target_system != 0 && c.target_system != system) break;
        ground_system = static_cast<uint8_t>(msg.sysid);
        ground_component = msg.compid;
        ack(c.command, command(c.command, c.param1, c.param2, c.param3));
        break;
      }
      case MAVLINK_MSG_ID_PARAM_REQUEST_LIST:
        send_all_params = true;
        next_param = 0;
        break;
      case MAVLINK_MSG_ID_PARAM_REQUEST_READ: {
        mavlink_param_request_read_t r;
        mavlink_msg_param_request_read_decode(&msg, &r);
        size_t index = 0;
        if (r.param_index >= 0 && static_cast<size_t>(r.param_index) < params.size()) {
          param_value(static_cast<size_t>(r.param_index));
        } else if (params.find(param_name(r.param_id), &index) != nullptr) {
          param_value(index);
        }
        break;
      }
      case MAVLINK_MSG_ID_PARAM_SET: {
        mavlink_param_set_t p;
        mavlink_msg_param_set_decode(&msg, &p);
        if (p.target_system != 0 && p.target_system != system) break;
        const std::string name = param_name(p.param_id);
        size_t index;
        if (p.param_type == MAV_PARAM_TYPE_REAL32) {
          index = params.set(name, p.param_value);
        } else {
          const float raw = p.param_value;
          int32_t i;
          std::memcpy(&i, &raw, sizeof(i));
          index = params.set_int(name, i);
        }
        param_value(index);  // the echo is the ground's confirmation
        break;
      }
      case MAVLINK_MSG_ID_SET_POSITION_TARGET_LOCAL_NED: {
        mavlink_set_position_target_local_ned_t s;
        mavlink_msg_set_position_target_local_ned_decode(&msg, &s);
        if (handlers.offboard)
          handlers.offboard({now_us, s.type_mask, {s.x, s.y, s.z}, {s.vx, s.vy, s.vz},
                             {s.afx, s.afy, s.afz}, s.yaw, s.yaw_rate});
        break;
      }
      case MAVLINK_MSG_ID_MANUAL_CONTROL: {
        mavlink_manual_control_t m;
        mavlink_msg_manual_control_decode(&msg, &m);
        if (handlers.manual)
          handlers.manual({now_us, m.x / 1000.0f, m.y / 1000.0f, m.z / 1000.0f, m.r / 1000.0f});
        break;
      }
      default:
        break;
    }
  }

  void stream(uint32_t id, const Telemetry& t) {
    mavlink_message_t msg;
    const auto boot_ms = static_cast<uint32_t>(t.t_us / 1000);
    switch (id) {
      case MAVLINK_MSG_ID_HEARTBEAT: {
        mavlink_heartbeat_t h{};
        h.type = MAV_TYPE_QUADROTOR;
        h.autopilot = kAutopilotPx4;
        h.base_mode = MAV_MODE_FLAG_CUSTOM_MODE_ENABLED | (t.armed ? MAV_MODE_FLAG_SAFETY_ARMED : 0);
        h.custom_mode = px4_custom_mode(t.mode);
        h.system_status = t.mode == Mode::Termination ? MAV_STATE_FLIGHT_TERMINATION
                          : t.armed                   ? MAV_STATE_ACTIVE
                                                      : MAV_STATE_STANDBY;
        h.mavlink_version = 3;
        mavlink_msg_heartbeat_encode(system, component, &msg, &h);
        break;
      }
      case MAVLINK_MSG_ID_SYS_STATUS: {
        mavlink_sys_status_t s{};
        s.onboard_control_sensors_present = sensors_present();
        s.onboard_control_sensors_enabled = sensors_present();
        uint32_t healthy = MAV_SYS_STATUS_SENSOR_3D_GYRO | MAV_SYS_STATUS_SENSOR_3D_ACCEL |
                           MAV_SYS_STATUS_SENSOR_3D_MAG | MAV_SYS_STATUS_SENSOR_ABSOLUTE_PRESSURE |
                           MAV_SYS_STATUS_SENSOR_MOTOR_OUTPUTS | MAV_SYS_STATUS_AHRS;
        if (t.gps_fix && t.global_valid) healthy |= MAV_SYS_STATUS_SENSOR_GPS;
        if (t.armable) healthy |= MAV_SYS_STATUS_PREARM_CHECK;
        s.onboard_control_sensors_health = healthy;
        s.voltage_battery = static_cast<uint16_t>(t.battery_v * 1000);
        s.current_battery = static_cast<int16_t>(t.battery_a * 100);
        s.battery_remaining =
            t.battery_remaining < 0 ? -1 : static_cast<int8_t>(std::lround(t.battery_remaining * 100));
        mavlink_msg_sys_status_encode(system, component, &msg, &s);
        break;
      }
      case MAVLINK_MSG_ID_EXTENDED_SYS_STATE: {
        mavlink_extended_sys_state_t e{};
        e.vtol_state = MAV_VTOL_STATE_UNDEFINED;
        e.landed_state = static_cast<uint8_t>(t.landed);
        mavlink_msg_extended_sys_state_encode(system, component, &msg, &e);
        break;
      }
      case MAVLINK_MSG_ID_ATTITUDE_QUATERNION: {
        mavlink_attitude_quaternion_t a{};
        a.time_boot_ms = boot_ms;
        a.q1 = t.attitude.w;
        a.q2 = t.attitude.x;
        a.q3 = t.attitude.y;
        a.q4 = t.attitude.z;
        a.rollspeed = t.rates.x;
        a.pitchspeed = t.rates.y;
        a.yawspeed = t.rates.z;
        mavlink_msg_attitude_quaternion_encode(system, component, &msg, &a);
        break;
      }
      case MAVLINK_MSG_ID_HIGHRES_IMU: {
        mavlink_highres_imu_t i{};
        i.time_usec = t.t_us;
        i.xacc = t.accel.x;
        i.yacc = t.accel.y;
        i.zacc = t.accel.z;
        i.xgyro = t.gyro.x;
        i.ygyro = t.gyro.y;
        i.zgyro = t.gyro.z;
        i.xmag = t.mag.x;
        i.ymag = t.mag.y;
        i.zmag = t.mag.z;
        i.abs_pressure = t.pressure_hpa;
        i.temperature = t.temperature_c;
        i.fields_updated = 0x1fff;
        mavlink_msg_highres_imu_encode(system, component, &msg, &i);
        break;
      }
      case MAVLINK_MSG_ID_LOCAL_POSITION_NED: {
        if (!t.position_valid) return;
        mavlink_local_position_ned_t p{};
        p.time_boot_ms = boot_ms;
        p.x = t.position.x;
        p.y = t.position.y;
        p.z = t.position.z;
        p.vx = t.velocity.x;
        p.vy = t.velocity.y;
        p.vz = t.velocity.z;
        mavlink_msg_local_position_ned_encode(system, component, &msg, &p);
        break;
      }
      case MAVLINK_MSG_ID_GLOBAL_POSITION_INT: {
        if (!t.global_valid) return;
        mavlink_global_position_int_t g{};
        g.time_boot_ms = boot_ms;
        g.lat = static_cast<int32_t>(std::llround(t.lat_deg * 1e7));
        g.lon = static_cast<int32_t>(std::llround(t.lon_deg * 1e7));
        g.alt = static_cast<int32_t>(std::lround(t.alt_msl_m * 1000));
        g.relative_alt = static_cast<int32_t>(std::lround(t.alt_rel_m * 1000));
        g.vx = static_cast<int16_t>(t.velocity.x * 100);
        g.vy = static_cast<int16_t>(t.velocity.y * 100);
        g.vz = static_cast<int16_t>(t.velocity.z * 100);
        float heading = t.attitude.yaw() * 180 / kPi;
        if (heading < 0) heading += 360;
        g.hdg = static_cast<uint16_t>(std::lround(heading * 100)) % 36000;
        mavlink_msg_global_position_int_encode(system, component, &msg, &g);
        break;
      }
      case MAVLINK_MSG_ID_GPS_RAW_INT: {
        mavlink_gps_raw_int_t g{};
        g.time_usec = t.t_us;
        g.fix_type = t.gps_fix ? GPS_FIX_TYPE_3D_FIX : GPS_FIX_TYPE_NO_FIX;
        g.lat = static_cast<int32_t>(std::llround(t.lat_deg * 1e7));
        g.lon = static_cast<int32_t>(std::llround(t.lon_deg * 1e7));
        g.alt = static_cast<int32_t>(std::lround(t.alt_msl_m * 1000));
        g.eph = g.epv = 100;  // cm
        g.vel = g.cog = UINT16_MAX;
        g.satellites_visible = t.satellites;
        mavlink_msg_gps_raw_int_encode(system, component, &msg, &g);
        break;
      }
      case MAVLINK_MSG_ID_HOME_POSITION: {
        if (!t.home_valid) return;
        mavlink_home_position_t h{};
        h.latitude = static_cast<int32_t>(std::llround(t.home_lat_deg * 1e7));
        h.longitude = static_cast<int32_t>(std::llround(t.home_lon_deg * 1e7));
        h.altitude = static_cast<int32_t>(std::lround(t.home_alt_msl_m * 1000));
        h.x = t.home_position.x;
        h.y = t.home_position.y;
        h.z = t.home_position.z;
        h.q[0] = 1;
        h.time_usec = t.t_us;
        mavlink_msg_home_position_encode(system, component, &msg, &h);
        break;
      }
      case MAVLINK_MSG_ID_BATTERY_STATUS: {
        if (t.battery_v <= 0) return;
        mavlink_battery_status_t b{};
        b.id = 0;
        b.battery_function = MAV_BATTERY_FUNCTION_ALL;
        b.type = MAV_BATTERY_TYPE_LION;
        b.temperature = INT16_MAX;
        for (int k = 0; k < 10; ++k) b.voltages[k] = UINT16_MAX;
        b.voltages[0] = static_cast<uint16_t>(t.battery_v * 1000);
        b.current_battery = static_cast<int16_t>(t.battery_a * 100);
        b.current_consumed = b.energy_consumed = -1;
        b.battery_remaining =
            t.battery_remaining < 0 ? -1 : static_cast<int8_t>(std::lround(t.battery_remaining * 100));
        mavlink_msg_battery_status_encode(system, component, &msg, &b);
        break;
      }
      case MAVLINK_MSG_ID_AUTOPILOT_VERSION: {
        mavlink_autopilot_version_t v{};
        v.capabilities = MAV_PROTOCOL_CAPABILITY_MAVLINK2 |
                         MAV_PROTOCOL_CAPABILITY_PARAM_ENCODE_BYTEWISE |
                         MAV_PROTOCOL_CAPABILITY_COMMAND_INT |
                         MAV_PROTOCOL_CAPABILITY_SET_POSITION_TARGET_LOCAL_NED;
        v.flight_sw_version = (0u << 24) | (1u << 16) | (0u << 8) | 0u;  // my 0.1.0, in development
        v.uid = 0x70637331340000ull | system;                          // "pcs14" and the system id
        mavlink_msg_autopilot_version_encode(system, component, &msg, &v);
        break;
      }
      default:
        return;
    }
    out(msg);
  }
};

Link::Link(Params& params, Send send, Handlers handlers, uint8_t system, uint8_t component)
    : impl_(std::make_unique<Impl>(params, std::move(send), std::move(handlers), system, component)) {}

Link::~Link() = default;

void Link::receive(const uint8_t* data, size_t size, uint64_t now_us) {
  for (size_t k = 0; k < size; ++k) {
    mavlink_message_t msg;
    mavlink_status_t status;
    if (mavlink_frame_char_buffer(&impl_->rx_buffer, &impl_->rx_status, data[k], &msg, &status) ==
        MAVLINK_FRAMING_OK)
      impl_->handle(msg, now_us);
  }
}

void Link::update(const Telemetry& t) {
  for (auto& [id, s] : impl_->streams) {
    if (s.interval_us == 0 || t.t_us < s.next_us) continue;
    // keep the rate even when updates come late, without a burst to catch up
    s.next_us = (s.next_us == 0 || t.t_us - s.next_us > s.interval_us) ? t.t_us + s.interval_us
                                                                       : s.next_us + s.interval_us;
    impl_->stream(id, t);
  }
  for (uint32_t id : impl_->once) impl_->stream(id, t);
  impl_->once.clear();
  // the parameter list goes out a few at a time, so it doesn't flood the link
  for (int k = 0; k < 5 && impl_->send_all_params && impl_->next_param < impl_->params.size(); ++k)
    impl_->param_value(impl_->next_param++);
  if (impl_->next_param >= impl_->params.size()) impl_->send_all_params = false;
}

void Link::status_text(uint8_t severity, const char* text) {
  mavlink_statustext_t s{};
  s.severity = severity;
  std::memcpy(s.text, text, std::min(std::strlen(text), sizeof(s.text)));
  mavlink_message_t msg;
  mavlink_msg_statustext_encode(impl_->system, impl_->component, &msg, &s);
  impl_->out(msg);
}

uint64_t Link::last_ground_heartbeat_us() const { return impl_->ground_heartbeat_us; }

}  // namespace pcs14
