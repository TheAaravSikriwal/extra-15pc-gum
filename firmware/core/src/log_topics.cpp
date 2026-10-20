// The logged topics. GPL-3.0.
#include "pcs14/log_topics.hpp"

namespace pcs14 {

FlightLogWriter::FlightLogWriter(ULogWriter& out, bool ground_truth)
    : out_(out), truth_(ground_truth) {
  if (truth_) {
    out_.format(
        "vehicle_local_position_groundtruth:uint64_t timestamp;float x;float y;float z;"
        "float vx;float vy;float vz;");
    out_.format("vehicle_attitude_groundtruth:uint64_t timestamp;float[4] q;");
  }
  out_.format("esc_report:int32_t esc_rpm;");
  out_.format("esc_status:uint64_t timestamp;uint8_t esc_count;esc_report[4] esc;");
  out_.format("sensor_combined:uint64_t timestamp;float[3] gyro_rad;float[3] accelerometer_m_s2;");
  out_.format("vehicle_status:uint64_t timestamp;uint8_t arming_state;uint8_t nav_state;");
  out_.format("vehicle_land_detected:uint64_t timestamp;bool landed;");
  out_.format(
      "failsafe_flags:uint64_t timestamp;bool gcs_connection_lost;bool global_position_invalid;"
      "bool fd_critical_failure;bool fd_motor_failure;uint8_t battery_warning;");
  out_.format("battery_status:uint64_t timestamp;float voltage_v;float current_a;float remaining;");
  if (truth_) {
    position_ = out_.subscribe("vehicle_local_position_groundtruth");
    attitude_ = out_.subscribe("vehicle_attitude_groundtruth");
  }
  esc_ = out_.subscribe("esc_status");
  imu_ = out_.subscribe("sensor_combined");
  status_ = out_.subscribe("vehicle_status");
  land_ = out_.subscribe("vehicle_land_detected");
  failsafe_ = out_.subscribe("failsafe_flags");
  battery_ = out_.subscribe("battery_status");
}

namespace {
Packer& put(Packer& p, const Vec3& v) { return p.put(v.x).put(v.y).put(v.z); }
}  // namespace

void FlightLogWriter::log(const TruthPosition& s) {
  if (!truth_) return;
  Packer p;
  p.put(s.t_us);
  put(put(p, s.position), s.velocity);
  out_.data(position_, p.data(), p.size());
}

void FlightLogWriter::log(const TruthAttitude& s) {
  if (!truth_) return;
  Packer p;
  p.put(s.t_us).put(s.q.w).put(s.q.x).put(s.q.y).put(s.q.z);
  out_.data(attitude_, p.data(), p.size());
}

void FlightLogWriter::log(const EscSample& s) {
  Packer p;
  p.put(s.t_us).put(static_cast<uint8_t>(4));
  for (float w : s.rad_s) p.put(static_cast<int32_t>(w + (w >= 0 ? 0.5f : -0.5f)));
  out_.data(esc_, p.data(), p.size());
}

void FlightLogWriter::log(const ImuLog& s) {
  Packer p;
  p.put(s.t_us);
  put(put(p, s.gyro), s.accel);
  out_.data(imu_, p.data(), p.size());
}

void FlightLogWriter::log(const StatusLog& s) {
  Packer p;
  p.put(s.t_us).put(s.arming_state).put(s.nav_state);
  out_.data(status_, p.data(), p.size());
}

void FlightLogWriter::log(const LandLog& s) {
  Packer p;
  p.put(s.t_us).put_bool(s.landed);
  out_.data(land_, p.data(), p.size());
}

void FlightLogWriter::log(const FailsafeLog& s) {
  Packer p;
  p.put(s.t_us)
      .put_bool(s.link_lost)
      .put_bool(s.position_invalid)
      .put_bool(s.critical_failure)
      .put_bool(s.motor_failure)
      .put(s.battery_warning);
  out_.data(failsafe_, p.data(), p.size());
}

void FlightLogWriter::log(const BatteryLog& s) {
  Packer p;
  p.put(s.t_us).put(s.voltage_v).put(s.current_a).put(s.remaining);
  out_.data(battery_, p.data(), p.size());
}

}  // namespace pcs14
