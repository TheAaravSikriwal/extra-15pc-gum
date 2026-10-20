// The sim layer: my firmware as a Linux program flying a Gazebo model, standing in for PX4 and
// its Gazebo bridge. GPL-3.0.
//
//   pcs14_sitl --world pcs14 --model pcs14_base_0 --airframe models/pcs14_base/firmware.txt
//              [--log log/sitl.ulg]
//
// The sensors are the model's own Gazebo sensors, the ones PX4 reads. Gazebo gives them in the
// body's forward-left-up frame; they turn into forward-right-down here. The loop runs once per
// IMU sample (250 Hz), the way PX4's runs on each gyro sample, and each run sends the four
// motor speeds on /<model>/command/motor_speed, which the motor plugins listen to.
//
// It writes a ULog with the topics the flight sim's graders read, ground truth included: the
// world's pose of the model, as PX4's bridge logs it. Times are Gazebo's clock, as in PX4's sim
// logs.
//
// Until MAVLink comes (step 5, task 6), commands come one per line on stdin:
//   arm | disarm | sticks <roll> <pitch> <yaw> <throttle> | quit
// It prints "ready" once the first IMU sample is in, and a status line every second of sim
// time. When stdin closes, it stops the motors and leaves.
#include <gz/msgs/actuators.pb.h>
#include <gz/msgs/imu.pb.h>
#include <gz/msgs/magnetometer.pb.h>
#include <gz/msgs/pose_v.pb.h>

#include <array>
#include <cmath>
#include <cstdio>
#include <filesystem>
#include <fstream>
#include <iostream>
#include <memory>
#include <mutex>
#include <sstream>
#include <string>

#include <gz/transport/Node.hh>

#include "pcs14/airframe_file.hpp"
#include "pcs14/flight.hpp"
#include "pcs14/log_topics.hpp"
#include "pcs14/ulog.hpp"

namespace {

using pcs14::Quat;
using pcs14::Vec3;

constexpr double kStatusEvery = 0.1;  // s of sim time between status, landed and failsafe samples

// Gazebo's body frame (forward-left-up) into mine (forward-right-down)
Vec3 frd(const gz::msgs::Vector3d& v) {
  return {static_cast<float>(v.x()), static_cast<float>(-v.y()), static_cast<float>(-v.z())};
}

// Gazebo's world (east-north-up) and body (forward-left-up) into north-east-down and
// forward-right-down: half a turn about (1, 1, 0) on the world side, and about x on the body's
Quat ned_frd(const gz::msgs::Quaternion& q) {
  const float s = std::sqrt(0.5f);
  const Quat world{0, s, s, 0}, body{0, 1, 0, 0};
  const Quat gz{static_cast<float>(q.w()), static_cast<float>(q.x()), static_cast<float>(q.y()),
                static_cast<float>(q.z())};
  return world * gz * body;
}

double seconds(const gz::msgs::Header& header) {
  return static_cast<double>(header.stamp().sec()) + header.stamp().nsec() * 1e-9;
}

uint64_t micros(double t) { return t > 0 ? static_cast<uint64_t>(std::llround(t * 1e6)) : 0; }

struct Options {
  std::string world = "pcs14", model, airframe, log = "log/sitl.ulg";
};

bool parse_options(int argc, char** argv, Options& o) {
  for (int k = 1; k + 1 < argc; k += 2) {
    const std::string key = argv[k], value = argv[k + 1];
    if (key == "--world") o.world = value;
    else if (key == "--model") o.model = value;
    else if (key == "--airframe") o.airframe = value;
    else if (key == "--log") o.log = value;
    else return false;
  }
  return !o.model.empty() && !o.airframe.empty();
}

class Bridge {
 public:
  Bridge(const pcs14::Airframe& airframe, const Options& o, std::FILE* log_file)
      : flight_(airframe),
        model_(o.model),
        file_(log_file),
        ulog_([this](const uint8_t* d, size_t n) {
          if (file_ != nullptr) std::fwrite(d, 1, n, file_);
        }) {
    ulog_.begin(0);
    ulog_.info("sys_name", "pcs14");
    ulog_.info("ver_hw", "SITL");
    log_ = std::make_unique<pcs14::FlightLogWriter>(ulog_, true);
    const std::string sensors =
        "/world/" + o.world + "/model/" + o.model + "/link/base_link/sensor/";
    // the motor plugins have no namespace set, so they listen under the model's own name
    motors_ = node_.Advertise<gz::msgs::Actuators>("/" + o.model + "/command/motor_speed");
    node_.Subscribe(sensors + "imu_sensor/imu", &Bridge::on_imu, this);
    node_.Subscribe(sensors + "magnetometer_sensor/magnetometer", &Bridge::on_mag, this);
    node_.Subscribe("/world/" + o.world + "/pose/info", &Bridge::on_poses, this);
  }

  bool command(const std::string& line) {
    std::istringstream words(line);
    std::string verb;
    if (!(words >> verb)) return true;
    std::lock_guard<std::mutex> lock(mutex_);
    if (verb == "arm") {
      flight_.arm();
      ulog_.text(6, micros(last_), "armed");
    } else if (verb == "disarm") {
      flight_.disarm();
      ulog_.text(6, micros(last_), "disarmed");
    } else if (verb == "sticks") {
      pcs14::Sticks s;
      if (!(words >> s.roll >> s.pitch >> s.yaw >> s.throttle)) {
        std::printf("error: sticks takes roll pitch yaw throttle\n");
      } else {
        flight_.set_sticks(s);
      }
    } else if (verb == "quit") {
      return false;
    } else {
      std::printf("error: no command %s\n", verb.c_str());
    }
    std::fflush(stdout);
    return true;
  }

  void stop() {
    std::lock_guard<std::mutex> lock(mutex_);
    flight_.disarm();
    send({});
    if (file_ != nullptr) std::fflush(file_);
  }

 private:
  void on_imu(const gz::msgs::IMU& msg) {
    std::lock_guard<std::mutex> lock(mutex_);
    const double t = seconds(msg.header());
    const float dt = static_cast<float>(t - last_);
    const bool first = last_ < 0;
    last_ = t;
    if (first) {
      // a first status sample before any command can come in, so the log shows the arming
      log_status(micros(t));
      std::printf("ready t=%.3f\n", t);
      std::fflush(stdout);
      return;
    }
    if (dt <= 0 || dt > 0.1f) return;  // a repeat or a jump in the clock: skip a beat
    const Vec3 gyro = frd(msg.angular_velocity()), accel = frd(msg.linear_acceleration());
    const pcs14::Mix mix = flight_.step(gyro, accel, dt);
    send(mix.rad_s);
    const uint64_t us = micros(t);
    log_->log(pcs14::ImuLog{us, gyro, accel});
    log_->log(pcs14::EscSample{us, mix.rad_s});
    if (t >= next_sample_) {
      next_sample_ = t + kStatusEvery;
      log_status(us);
    }
    if (t >= next_status_) {
      next_status_ = t + 1.0;
      const Quat& q = flight_.attitude().q();
      std::printf("t=%.3f armed=%d roll=%.2f pitch=%.2f yaw=%.1f motors=%.0f %.0f %.0f %.0f\n", t,
                  flight_.armed() ? 1 : 0, q.roll() * 180 / pcs14::kPi,
                  q.pitch() * 180 / pcs14::kPi, q.yaw() * 180 / pcs14::kPi, mix.rad_s[0],
                  mix.rad_s[1], mix.rad_s[2], mix.rad_s[3]);
      std::fflush(stdout);
    }
  }

  void log_status(uint64_t us) {
    log_->log(pcs14::StatusLog{
        us, flight_.armed() ? pcs14::kArmingArmed : pcs14::kArmingStandby, pcs14::kNavAcro});
    log_->log(pcs14::LandLog{us, flight_.on_ground()});
    log_->log(pcs14::FailsafeLog{us});
  }

  void on_mag(const gz::msgs::Magnetometer& msg) {
    std::lock_guard<std::mutex> lock(mutex_);
    flight_.on_mag(frd(msg.field_tesla()));
  }

  // the ground truth, from the world's poses (east-north-up there, north-east-down here)
  void on_poses(const gz::msgs::Pose_V& msg) {
    for (const auto& pose : msg.pose()) {
      if (pose.name() != model_) continue;
      std::lock_guard<std::mutex> lock(mutex_);
      const double t = seconds(msg.header());
      const Vec3 p{static_cast<float>(pose.position().y()), static_cast<float>(pose.position().x()),
                   static_cast<float>(-pose.position().z())};
      Vec3 v;
      if (truth_t_ >= 0 && t > truth_t_) v = (p - truth_p_) / static_cast<float>(t - truth_t_);
      if (truth_t_ < 0 || t > truth_t_) {
        log_->log(pcs14::TruthPosition{micros(t), p, v});
        log_->log(pcs14::TruthAttitude{micros(t), ned_frd(pose.orientation())});
        truth_t_ = t;
        truth_p_ = p;
      }
      return;
    }
  }

  void send(const std::array<float, 4>& speeds) {
    gz::msgs::Actuators out;
    for (float w : speeds) out.add_velocity(w);
    motors_.Publish(out);
  }

  pcs14::Flight flight_;
  std::string model_;
  std::FILE* file_;
  pcs14::ULogWriter ulog_;
  std::unique_ptr<pcs14::FlightLogWriter> log_;
  gz::transport::Node node_;
  gz::transport::Node::Publisher motors_;
  std::mutex mutex_;
  double last_ = -1, next_status_ = 0, next_sample_ = 0;
  double truth_t_ = -1;
  Vec3 truth_p_;
};

}  // namespace

int main(int argc, char** argv) {
  Options options;
  if (!parse_options(argc, argv, options)) {
    std::fprintf(stderr,
                 "usage: pcs14_sitl [--world pcs14] --model <name in Gazebo> --airframe <file> "
                 "[--log log/sitl.ulg]\n");
    return 2;
  }
  std::ifstream file(options.airframe);
  std::stringstream text;
  text << file.rdbuf();
  pcs14::Airframe airframe;
  std::string error;
  if (!file || !pcs14::parse_airframe(text.str(), airframe, error)) {
    std::fprintf(stderr, "%s: %s\n", options.airframe.c_str(),
                 file ? error.c_str() : "can't read it");
    return 2;
  }
  const std::filesystem::path log_path(options.log);
  if (log_path.has_parent_path()) std::filesystem::create_directories(log_path.parent_path());
  std::FILE* log_file = std::fopen(options.log.c_str(), "wb");
  if (log_file == nullptr) {
    std::fprintf(stderr, "%s: can't write the log there\n", options.log.c_str());
    return 2;
  }
  {
    Bridge bridge(airframe, options, log_file);
    std::string line;
    while (std::getline(std::cin, line) && bridge.command(line)) {
    }
    bridge.stop();
  }
  std::fclose(log_file);
  return 0;
}
