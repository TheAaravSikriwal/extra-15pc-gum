// The safety monitor in the sim: the Teensy's core on its own simulated IMU, between my
// flight controller and the motors. GPL-3.0.
//
//   pcs14_monitor_sitl --world pcs14 --model pcs14_base_0 [--live]
//
// On the drone the Teensy sits on the ESC signal lines: it passes the flight controller's DShot
// through, and when it cuts it takes the lines over and sends stop frames. Here the flight
// controller's motor speeds come in on /<model>/fc/motor_speed (pcs14_sitl --monitor sends
// them there), the monitor passes them on to /<model>/command/motor_speed, and once it cuts it
// sends zeros instead, at its own rate, whatever the flight controller does. Gazebo's motors
// hold their last command forever, so without those zeros a hung flight controller would
// leave the motors at their last speed: exactly what the monitor is there to prevent.
//
// The flight controller's heartbeat comes on /<model>/fc/heartbeat (its armed state), and the
// kill switch on /<model>/kill. Its own heartbeat goes out on /<model>/monitor/heartbeat,
// carrying whether it's cutting: the flight controller won't arm without it. Its triggers run
// in shadow mode unless --live. It prints a line when it cuts and for every trigger, which is
// its log.
#include <gz/msgs/actuators.pb.h>
#include <gz/msgs/boolean.pb.h>
#include <gz/msgs/imu.pb.h>

#include <atomic>
#include <chrono>
#include <csignal>
#include <cstdio>
#include <mutex>
#include <string>
#include <thread>

#include <gz/transport/Node.hh>

#include "pcs14/monitor.hpp"

namespace {

std::atomic<bool> g_stop{false};

pcs14::Vec3 frd(const gz::msgs::Vector3d& v) {
  return {static_cast<float>(v.x()), static_cast<float>(-v.y()), static_cast<float>(-v.z())};
}

double seconds(const gz::msgs::Header& h) {
  return static_cast<double>(h.stamp().sec()) + h.stamp().nsec() * 1e-9;
}

class MonitorBridge {
 public:
  MonitorBridge(const std::string& world, const std::string& model, bool live)
      : monitor_(settings(live)) {
    motors_ = node_.Advertise<gz::msgs::Actuators>("/" + model + "/command/motor_speed");
    heartbeat_out_ = node_.Advertise<gz::msgs::Boolean>("/" + model + "/monitor/heartbeat");
    node_.Subscribe("/world/" + world + "/model/" + model +
                        "/link/base_link/sensor/monitor_imu_sensor/imu",
                    &MonitorBridge::on_imu, this);
    node_.Subscribe("/" + model + "/fc/motor_speed", &MonitorBridge::on_fc_motors, this);
    node_.Subscribe("/" + model + "/fc/heartbeat", &MonitorBridge::on_heartbeat, this);
    node_.Subscribe("/" + model + "/kill", &MonitorBridge::on_kill, this);
  }

 private:
  static pcs14::MonitorSettings settings(bool live) {
    pcs14::MonitorSettings s;
    s.shadow = !live;
    return s;
  }

  void on_imu(const gz::msgs::IMU& msg) {
    std::lock_guard<std::mutex> lock(mutex_);
    const double t = seconds(msg.header());
    const float dt = last_ < 0 ? 0.004f : static_cast<float>(t - last_);
    last_ = t;
    if (dt <= 0) return;
    const size_t before = monitor_.triggers().size();
    const bool was = monitor_.cutting();
    monitor_.update(t, frd(msg.angular_velocity()), frd(msg.linear_acceleration()), heartbeat_,
                    armed_, kill_, dt);
    heartbeat_ = false;
    for (size_t k = before; k < monitor_.triggers().size(); ++k) {
      const pcs14::Trigger& tr = monitor_.triggers()[k];
      std::printf("trigger %s at %.3f since %.3f\n", pcs14::trigger_name(tr.kind), tr.at,
                  tr.since);
    }
    if (monitor_.cutting() && !was)
      std::printf("cut %s at %.3f\n", pcs14::cut_name(monitor_.why()), monitor_.cut_at());
    if (!monitor_.cutting() && was) std::printf("cut cleared at %.3f\n", t);
    std::fflush(stdout);
    if (++beats_ % kHeartbeatEvery == 0) {  // 25 Hz, on its own clock
      gz::msgs::Boolean beat;
      beat.set_data(monitor_.cutting());
      heartbeat_out_.Publish(beat);
    }
    // cutting: stop frames, every step, on the monitor's own clock
    if (monitor_.cutting()) {
      gz::msgs::Actuators stop;
      for (int i = 0; i < 4; ++i) stop.add_velocity(0);
      motors_.Publish(stop);
    }
  }

  void on_fc_motors(const gz::msgs::Actuators& msg) {
    std::lock_guard<std::mutex> lock(mutex_);
    if (!monitor_.cutting()) motors_.Publish(msg);  // the lines pass straight through
  }

  void on_heartbeat(const gz::msgs::Boolean& msg) {
    std::lock_guard<std::mutex> lock(mutex_);
    heartbeat_ = true;
    armed_ = msg.data();
  }

  void on_kill(const gz::msgs::Boolean& msg) {
    std::lock_guard<std::mutex> lock(mutex_);
    kill_ = msg.data();
  }

  pcs14::Monitor monitor_;
  gz::transport::Node node_;
  gz::transport::Node::Publisher motors_, heartbeat_out_;
  static constexpr int kHeartbeatEvery = 10;  // IMU samples (250 Hz) between heartbeats
  int beats_ = 0;
  std::mutex mutex_;
  double last_ = -1;
  bool heartbeat_ = false, armed_ = false, kill_ = false;
};

}  // namespace

int main(int argc, char** argv) {
  std::string world = "pcs14", model;
  bool live = false;
  for (int k = 1; k < argc; ++k) {
    const std::string a = argv[k];
    if (a == "--live") live = true;
    else if (a == "--world" && k + 1 < argc) world = argv[++k];
    else if (a == "--model" && k + 1 < argc) model = argv[++k];
  }
  if (model.empty()) {
    std::fprintf(stderr, "usage: pcs14_monitor_sitl [--world pcs14] --model <name> [--live]\n");
    return 2;
  }
  std::signal(SIGTERM, [](int) { g_stop = true; });
  std::signal(SIGINT, [](int) { g_stop = true; });
  MonitorBridge bridge(world, model, live);
  std::printf("monitor ready\n");
  std::fflush(stdout);
  while (!g_stop) std::this_thread::sleep_for(std::chrono::milliseconds(50));
  return 0;
}
