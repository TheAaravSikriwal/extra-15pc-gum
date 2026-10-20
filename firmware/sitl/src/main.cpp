// The sim layer: my firmware as a Linux program flying a Gazebo model, standing in for PX4 and
// its Gazebo bridge. GPL-3.0.
//
//   pcs14_sitl --world pcs14 --model pcs14_base_0 --airframe models/pcs14_base/firmware.txt
//              [--instance 0] [--params params.txt] [--log log/sitl.ulg] [--stdin]
//
// The sensors are the model's own Gazebo sensors, the ones PX4 reads. Gazebo gives them in the
// body's forward-left-up frame and an east-north-up world; they turn into forward-right-down
// and north-east-down here. The loop runs once per IMU sample (250 Hz), the way PX4's runs on
// each gyro sample, and each run sends the four motor speeds on /<model>/command/motor_speed,
// which the motor plugins listen to.
//
// MAVLink goes over UDP on PX4's ports for the same instance, so the flight sim's runner
// treats it like PX4: it listens on 14580 + instance and sends to 14540 + instance. The
// parameters file holds "NAME value" lines, PX4's names, loaded over the firmware's defaults.
//
// It writes a ULog with the topics the flight sim's graders read, ground truth included: the
// world's pose of the model, as PX4's bridge logs it. Times are Gazebo's clock, as in PX4's sim
// logs.
//
// With --stdin, commands also come one per line on stdin, for tests and poking at it:
//   arm | disarm | sticks <roll> <pitch> <yaw> <throttle> | quit
// and when stdin closes it stops. Without it, it runs until it's told to stop (SIGTERM).
// Either way it prints "ready" once the first IMU sample is in, and a status line every second
// of sim time.
#include <arpa/inet.h>
#include <gz/msgs/actuators.pb.h>
#include <gz/msgs/fluid_pressure.pb.h>
#include <gz/msgs/imu.pb.h>
#include <gz/msgs/magnetometer.pb.h>
#include <gz/msgs/navsat.pb.h>
#include <gz/msgs/pose_v.pb.h>
#include <netinet/in.h>
#include <sys/socket.h>
#include <unistd.h>

#include <array>
#include <atomic>
#include <cmath>
#include <csignal>
#include <cstdio>
#include <filesystem>
#include <fstream>
#include <iostream>
#include <memory>
#include <mutex>
#include <sstream>
#include <string>
#include <thread>

#include <gz/transport/Node.hh>

#include "pcs14/airframe_file.hpp"
#include "pcs14/flight.hpp"
#include "pcs14/link.hpp"
#include "pcs14/log_topics.hpp"
#include "pcs14/modes.hpp"
#include "pcs14/params.hpp"
#include "pcs14/ulog.hpp"

namespace {

using pcs14::Quat;
using pcs14::Vec3;

constexpr double kStatusEvery = 0.1;  // s of sim time between status, landed and failsafe samples
constexpr int kApiPort = 14540, kLocalPort = 14580;  // PX4's API link, plus the instance
constexpr double kEarthRadius = 6371000.0;           // m, for positions near home
std::atomic<bool> g_stop{false};

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
  std::string world = "pcs14", model, airframe, params, log = "log/sitl.ulg";
  int instance = 0;
  bool stdin_commands = false;
};

bool parse_options(int argc, char** argv, Options& o) {
  for (int k = 1; k < argc; ++k) {
    const std::string key = argv[k];
    if (key == "--stdin") {
      o.stdin_commands = true;
      continue;
    }
    if (k + 1 >= argc) return false;
    const std::string value = argv[++k];
    if (key == "--world") o.world = value;
    else if (key == "--model") o.model = value;
    else if (key == "--airframe") o.airframe = value;
    else if (key == "--params") o.params = value;
    else if (key == "--log") o.log = value;
    else if (key == "--instance") o.instance = std::stoi(value);
    else return false;
  }
  return !o.model.empty() && !o.airframe.empty();
}

bool read_text(const std::string& path, std::string& text) {
  std::ifstream file(path);
  if (!file) return false;
  std::stringstream s;
  s << file.rdbuf();
  text = s.str();
  return true;
}

// "NAME value" lines: an integer without a decimal point is an int32 parameter, like PX4's
void load_params(const std::string& text, pcs14::Params& params) {
  std::istringstream lines(text);
  std::string line;
  while (std::getline(lines, line)) {
    std::istringstream words(line);
    std::string name, value;
    if (!(words >> name >> value) || name[0] == '#') continue;
    if (value.find_first_of(".eE") == std::string::npos) params.set_int(name, std::stoi(value));
    else params.set(name, std::stof(value));
  }
}

// the firmware's own parameters, with PX4's names where PX4 has one
void default_params(pcs14::Params& p) {
  const pcs14::AutoSettings a;
  p.add("MIS_TAKEOFF_ALT", a.takeoff_height);  // m, what MAVSDK's set_takeoff_altitude sets
  p.add("MPC_TKO_SPEED", a.takeoff_speed);
  p.add("MPC_Z_V_AUTO_UP", a.climb_speed);
  p.add("MPC_Z_V_AUTO_DN", a.descent_speed);
  p.add("MPC_LAND_SPEED", a.land_speed);
  p.add("MPC_LAND_ALT1", a.land_slow_height);
  p.add("MPC_LAND_ALT2", a.land_slowest_height);
  p.add("MPC_XY_CRUISE", a.cruise_speed);
  p.add("MPC_VEL_MANUAL", a.manual_speed);
  p.add("RTL_RETURN_ALT", a.return_height);
  p.add("COM_OF_LOSS_T", a.offboard_loss_s);  // s without offboard setpoints before it's lost
  p.add_int("SYS_FAILURE_EN", 0);             // failure injection allowed
  p.add("COM_DL_LOSS_T", 10.0f);  // s without the ground's heartbeat before the link is lost
}

// the automatic modes' settings, from the parameters as they are now
pcs14::AutoSettings auto_settings(const pcs14::Params& p) {
  pcs14::AutoSettings a;
  a.takeoff_height = p.get("MIS_TAKEOFF_ALT", a.takeoff_height);
  a.takeoff_speed = p.get("MPC_TKO_SPEED", a.takeoff_speed);
  a.climb_speed = p.get("MPC_Z_V_AUTO_UP", a.climb_speed);
  a.descent_speed = p.get("MPC_Z_V_AUTO_DN", a.descent_speed);
  a.land_speed = p.get("MPC_LAND_SPEED", a.land_speed);
  a.land_slow_height = p.get("MPC_LAND_ALT1", a.land_slow_height);
  a.land_slowest_height = p.get("MPC_LAND_ALT2", a.land_slowest_height);
  a.cruise_speed = p.get("MPC_XY_CRUISE", a.cruise_speed);
  a.manual_speed = p.get("MPC_VEL_MANUAL", a.manual_speed);
  a.return_height = p.get("RTL_RETURN_ALT", a.return_height);
  a.offboard_loss_s = p.get("COM_OF_LOSS_T", a.offboard_loss_s);
  return a;
}

// the flight gains PX4's parameters set (the ones the generator writes)
pcs14::FlightGains flight_gains(const pcs14::Params& p) {
  pcs14::FlightGains g;
  g.angle.kp_roll_pitch = p.get("MC_ROLL_P", g.angle.kp_roll_pitch);
  g.angle.kp_yaw = p.get("MC_YAW_P", g.angle.kp_yaw);
  g.position.max_speed = p.get("MPC_XY_VEL_MAX", g.position.max_speed);
  g.position.max_tilt = p.get("MPC_TILTMAX_AIR", 45.0f) * pcs14::kPi / 180;
  return g;
}

// MAVLink over UDP on the loopback
class Udp {
 public:
  explicit Udp(int instance) {
    fd_ = socket(AF_INET, SOCK_DGRAM, 0);
    sockaddr_in local{};
    local.sin_family = AF_INET;
    local.sin_addr.s_addr = htonl(INADDR_LOOPBACK);
    local.sin_port = htons(static_cast<uint16_t>(kLocalPort + instance));
    bind(fd_, reinterpret_cast<sockaddr*>(&local), sizeof(local));
    timeval timeout{0, 100000};
    setsockopt(fd_, SOL_SOCKET, SO_RCVTIMEO, &timeout, sizeof(timeout));
    remote_.sin_family = AF_INET;
    remote_.sin_addr.s_addr = htonl(INADDR_LOOPBACK);
    remote_.sin_port = htons(static_cast<uint16_t>(kApiPort + instance));
  }
  ~Udp() { close(fd_); }
  void send(const uint8_t* data, size_t size) {
    sendto(fd_, data, size, 0, reinterpret_cast<const sockaddr*>(&remote_), sizeof(remote_));
  }
  // waits up to 0.1 s; returns the bytes read, or 0
  size_t receive(uint8_t* data, size_t size) {
    const ssize_t n = recv(fd_, data, size, 0);
    return n > 0 ? static_cast<size_t>(n) : 0;
  }

 private:
  int fd_;
  sockaddr_in remote_{};
};

class Bridge {
 public:
  Bridge(const pcs14::Airframe& airframe, const Options& o, pcs14::Params& params,
         std::FILE* log_file)
      : flight_(airframe, flight_gains(params)),
        params_(params),
        model_(o.model),
        file_(log_file),
        ulog_([this](const uint8_t* d, size_t n) {
          if (file_ != nullptr) std::fwrite(d, 1, n, file_);
        }),
        udp_(o.instance),
        link_(params, [this](const uint8_t* d, size_t n) { udp_.send(d, n); }, handlers()) {
    ulog_.begin(0);
    ulog_.info("sys_name", "pcs14");
    ulog_.info("ver_hw", "SITL");
    for (size_t k = 0; k < params_.size(); ++k) {
      const pcs14::Params::Param& p = params_.at(k);
      if (p.type == pcs14::Params::Type::Float) ulog_.parameter(p.name, p.f);
      else ulog_.parameter(p.name, p.i);
    }
    log_ = std::make_unique<pcs14::FlightLogWriter>(ulog_, true);
    const std::string sensors =
        "/world/" + o.world + "/model/" + o.model + "/link/base_link/sensor/";
    // the motor plugins have no namespace set, so they listen under the model's own name
    motors_ = node_.Advertise<gz::msgs::Actuators>("/" + o.model + "/command/motor_speed");
    node_.Subscribe(sensors + "imu_sensor/imu", &Bridge::on_imu, this);
    node_.Subscribe(sensors + "magnetometer_sensor/magnetometer", &Bridge::on_mag, this);
    node_.Subscribe(sensors + "air_pressure_sensor/air_pressure", &Bridge::on_pressure, this);
    node_.Subscribe(sensors + "navsat_sensor/navsat", &Bridge::on_navsat, this);
    node_.Subscribe("/world/" + o.world + "/pose/info", &Bridge::on_poses, this);
    listener_ = std::thread([this] { listen(); });
  }

  ~Bridge() {
    g_stop = true;
    if (listener_.joinable()) listener_.join();
  }

  bool command(const std::string& line) {
    std::istringstream words(line);
    std::string verb;
    if (!(words >> verb)) return true;
    std::lock_guard<std::mutex> lock(mutex_);
    if (verb == "arm") {
      arm();
    } else if (verb == "disarm") {
      disarm();
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
  pcs14::Link::Handlers handlers() {
    pcs14::Link::Handlers h;
    // called with the mutex held (from listen(), through Link::receive)
    h.request = [this](const pcs14::Request& r) { return request(r); };
    h.manual = [this](const pcs14::ManualInput& m) {
      // MANUAL_CONTROL's x is the pitch stick (forward is nose down), y roll, r yaw, z throttle
      flight_.set_sticks({m.y, -m.x, m.r, m.z});
    };
    h.offboard = [this](const pcs14::OffboardSetpoint& o) {
      // POSITION_TARGET_TYPEMASK: the bits are the fields to ignore
      constexpr uint16_t kPosition = 0x7, kVelocity = 0x38, kYaw = 0x400;
      pcs14::OffboardTarget t;
      t.position = (o.ignore & kPosition) == 0;
      t.point = o.position;
      if ((o.ignore & kVelocity) == 0) t.velocity = o.velocity;
      t.yaw = (o.ignore & kYaw) == 0 ? o.yaw : flight_.attitude().q().yaw();
      flight_.set_offboard(t);
    };
    return h;
  }

  bool armable() const { return have_imu_ && have_gps_; }

  void arm() {
    flight_.arm();
    ulog_.text(6, micros(last_), "armed");
  }

  void disarm() {
    flight_.disarm();
    ulog_.text(6, micros(last_), "disarmed");
  }

  // what the ground asks for: arming, the modes, take-off, land and return. Termination and
  // failure injection come with the failsafes (task 9); until then the ground hears "denied"
  bool request(const pcs14::Request& r) {
    using K = pcs14::Request::Kind;
    switch (r.kind) {
      case K::Arm:
        if (!armable()) return false;
        arm();
        return true;
      case K::Disarm:
        if (!flight_.on_ground()) return false;  // as PX4: not in the air, unless forced
        disarm();
        return true;
      case K::ForceDisarm:
        disarm();
        return true;
      case K::SetMode:
        return flight_.set_mode(r.mode);
      case K::Takeoff:
        return flight_.set_mode(pcs14::Mode::Takeoff);
      case K::Land:
        return flight_.set_mode(pcs14::Mode::Land);
      case K::Return:
        return flight_.set_mode(pcs14::Mode::Return);
      default:
        return false;
    }
  }

  void listen() {
    uint8_t buffer[2048];
    while (!g_stop) {
      const size_t n = udp_.receive(buffer, sizeof(buffer));
      if (n == 0) continue;
      std::lock_guard<std::mutex> lock(mutex_);
      link_.receive(buffer, n, micros(last_));
    }
  }

  void on_imu(const gz::msgs::IMU& msg) {
    std::lock_guard<std::mutex> lock(mutex_);
    const double t = seconds(msg.header());
    const float dt = static_cast<float>(t - last_);
    const bool first = last_ < 0;
    last_ = t;
    const Vec3 gyro = frd(msg.angular_velocity()), accel = frd(msg.linear_acceleration());
    if (first) {
      have_imu_ = true;
      // a first status sample before any command can come in, so the log shows the arming
      log_status(micros(t));
      std::printf("ready t=%.3f\n", t);
      std::fflush(stdout);
      return;
    }
    if (dt <= 0 || dt > 0.1f) return;  // a repeat or a jump in the clock: skip a beat
    flight_.set_auto(auto_settings(params_));
    const pcs14::Mix mix = flight_.step(gyro, accel, dt);
    send(mix.rad_s);
    const uint64_t us = micros(t);
    log_->log(pcs14::ImuLog{us, gyro, accel});
    log_->log(pcs14::EscSample{us, mix.rad_s});
    if (t >= next_sample_) {
      next_sample_ = t + kStatusEvery;
      log_status(us);
    }
    telemetry_.t_us = us;
    telemetry_.gyro = gyro;
    telemetry_.accel = accel;
    telemetry_.attitude = flight_.attitude().q();
    telemetry_.rates = flight_.attitude().rate();
    telemetry_.armed = flight_.armed();
    telemetry_.mode = flight_.mode();
    telemetry_.landed = flight_.on_ground() ? pcs14::Landed::OnGround : pcs14::Landed::InAir;
    telemetry_.armable = armable();
    telemetry_.position_valid = flight_.position_valid();
    telemetry_.position = flight_.position();
    telemetry_.velocity = flight_.velocity();
    if (flight_.home_valid()) telemetry_.home_position = flight_.home();
    link_.update(telemetry_);
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
        us, flight_.armed() ? pcs14::kArmingArmed : pcs14::kArmingStandby,
        pcs14::nav_state(flight_.mode())});
    log_->log(pcs14::LandLog{us, flight_.on_ground()});
    log_->log(pcs14::FailsafeLog{us});
  }

  void on_mag(const gz::msgs::Magnetometer& msg) {
    std::lock_guard<std::mutex> lock(mutex_);
    // Gazebo Harmonic's magnetometer, despite the field's name, gives gauss in a left-handed
    // frame (gz-sim pull request 2460); PX4's bridge maps it to forward-right-down as
    // (-y, -x, z), and so does this. Read as forward-left-up, the heading came out a quarter
    // turn wrong and the position loop spiralled
    const gz::msgs::Vector3d& f = msg.field_tesla();
    const Vec3 field{static_cast<float>(-f.y()), static_cast<float>(-f.x()),
                     static_cast<float>(f.z())};
    flight_.on_mag(field);
    telemetry_.mag = field;  // gauss, as MAVLink carries it
  }

  void on_pressure(const gz::msgs::FluidPressure& msg) {
    std::lock_guard<std::mutex> lock(mutex_);
    const double t = seconds(msg.header());
    flight_.on_baro(static_cast<float>(msg.pressure()),
                    baro_t_ >= 0 ? static_cast<float>(t - baro_t_) : 0.0f);
    baro_t_ = t;
    telemetry_.pressure_hpa = static_cast<float>(msg.pressure() / 100.0);
  }

  // The GPS: the first fix is the local origin (and the home MAVSDK sees before arming), and
  // each fix's offset from it, on a flat earth, goes to the position filter.
  void on_navsat(const gz::msgs::NavSat& msg) {
    std::lock_guard<std::mutex> lock(mutex_);
    Telemetry& t = telemetry_;
    if (!have_gps_) {
      have_gps_ = true;
      t.home_valid = true;
      t.home_lat_deg = msg.latitude_deg();
      t.home_lon_deg = msg.longitude_deg();
      t.home_alt_msl_m = static_cast<float>(msg.altitude());
    }
    t.gps_fix = true;
    t.satellites = 12;
    t.global_valid = true;
    t.lat_deg = msg.latitude_deg();
    t.lon_deg = msg.longitude_deg();
    t.alt_msl_m = static_cast<float>(msg.altitude());
    t.alt_rel_m = t.alt_msl_m - t.home_alt_msl_m;
    const double rad = pcs14::kPi / 180.0;
    const auto north = static_cast<float>((t.lat_deg - t.home_lat_deg) * rad * kEarthRadius);
    const auto east = static_cast<float>((t.lon_deg - t.home_lon_deg) * rad * kEarthRadius *
                                         std::cos(t.home_lat_deg * rad));
    const Vec3 velocity{static_cast<float>(msg.velocity_north()),
                        static_cast<float>(msg.velocity_east()),
                        static_cast<float>(-msg.velocity_up())};
    const double now = seconds(msg.header());
    // the fix's offset from home goes to the position filter; the telemetry carries its estimate
    flight_.on_gps(north, east, velocity, gps_t_ >= 0 ? static_cast<float>(now - gps_t_) : 0.0f);
    gps_t_ = now;
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

  using Telemetry = pcs14::Telemetry;
  pcs14::Flight flight_;
  pcs14::Params& params_;
  std::string model_;
  std::FILE* file_;
  pcs14::ULogWriter ulog_;
  std::unique_ptr<pcs14::FlightLogWriter> log_;
  Udp udp_;
  pcs14::Link link_;
  Telemetry telemetry_;
  gz::transport::Node node_;
  gz::transport::Node::Publisher motors_;
  std::mutex mutex_;
  std::thread listener_;
  double last_ = -1, next_status_ = 0, next_sample_ = 0;
  double truth_t_ = -1, baro_t_ = -1, gps_t_ = -1;
  Vec3 truth_p_;
  bool have_imu_ = false, have_gps_ = false;
};

}  // namespace

int main(int argc, char** argv) {
  Options options;
  if (!parse_options(argc, argv, options)) {
    std::fprintf(stderr,
                 "usage: pcs14_sitl [--world pcs14] --model <name in Gazebo> --airframe <file> "
                 "[--instance 0] [--params <file>] [--log log/sitl.ulg] [--stdin]\n");
    return 2;
  }
  std::string text;
  pcs14::Airframe airframe;
  std::string error;
  if (!read_text(options.airframe, text) || !pcs14::parse_airframe(text, airframe, error)) {
    std::fprintf(stderr, "%s: %s\n", options.airframe.c_str(),
                 error.empty() ? "can't read it" : error.c_str());
    return 2;
  }
  pcs14::Params params;
  default_params(params);
  if (!options.params.empty()) {
    if (!read_text(options.params, text)) {
      std::fprintf(stderr, "%s: can't read it\n", options.params.c_str());
      return 2;
    }
    load_params(text, params);
  }
  const std::filesystem::path log_path(options.log);
  if (log_path.has_parent_path()) std::filesystem::create_directories(log_path.parent_path());
  std::FILE* log_file = std::fopen(options.log.c_str(), "wb");
  if (log_file == nullptr) {
    std::fprintf(stderr, "%s: can't write the log there\n", options.log.c_str());
    return 2;
  }
  std::signal(SIGTERM, [](int) { g_stop = true; });
  std::signal(SIGINT, [](int) { g_stop = true; });
  {
    Bridge bridge(airframe, options, params, log_file);
    if (options.stdin_commands) {
      std::string line;
      while (!g_stop && std::getline(std::cin, line) && bridge.command(line)) {
      }
    } else {
      while (!g_stop) std::this_thread::sleep_for(std::chrono::milliseconds(50));
    }
    bridge.stop();
  }
  std::fclose(log_file);
  return 0;
}
