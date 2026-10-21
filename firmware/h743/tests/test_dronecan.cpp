// DroneCAN on the ARK FPV's CAN bus: two nodes, both libcanard, talking frame by frame.
#include <doctest/doctest.h>

#include <algorithm>
#include <vector>

#include "pcs14/h743/dronecan.hpp"

using namespace pcs14;
using namespace pcs14::dronecan;

namespace {
// moves every frame one node has queued onto the other
void carry(Node& from, Node& to, uint64_t now_us) {
  Frame f;
  while (from.next_frame(f)) to.receive(f, now_us);
}
}  // namespace

TEST_CASE("NodeStatus packs the way the DSDL lays it out") {
  // uptime uint32, then health uint2, mode uint3, sub_mode uint3, then vendor code uint16
  NodeStatus s{123456, Health::Warning, NodeMode::Operational, 0, 0xBEEF};
  uint8_t bytes[kNodeStatusBytes];
  encode(s, bytes);
  const NodeStatus back = decode_node_status(bytes, kNodeStatusBytes);
  CHECK(back.uptime_s == 123456);
  CHECK(back.health == Health::Warning);
  CHECK(back.mode == NodeMode::Operational);
  CHECK(back.vendor_code == 0xBEEF);
  CHECK(bytes[0] == 0x40);  // 123456 is 0x0001E240, low byte first
  CHECK(bytes[1] == 0xE2);
}

TEST_CASE("a node's heartbeat reaches the other, which knows it's alive and healthy") {
  Node fc(kFlightControllerId), gps(kGpsId);
  fc.update(1000000, Health::Ok, NodeMode::Operational);
  gps.update(1000000, Health::Ok, NodeMode::Operational);
  carry(gps, fc, 1000100);
  CHECK(fc.alive(kGpsId, 1500000));
  REQUIRE(fc.status(kGpsId) != nullptr);
  CHECK(fc.status(kGpsId)->health == Health::Ok);
  CHECK_FALSE(fc.alive(42, 1500000));  // never heard
}

TEST_CASE("it sends its own status once a second, and a node gone quiet for 3 s is offline") {
  Node fc(kFlightControllerId), gps(kGpsId);
  int sent = 0;
  for (uint64_t t = 0; t <= 5000000; t += 10000) {  // 5 s at 100 Hz
    fc.update(t, Health::Ok, NodeMode::Operational);
    Frame f;
    while (fc.next_frame(f)) ++sent;
  }
  CHECK(sent == 6);  // at 0, 1, 2, 3, 4 and 5 s
  gps.update(1000000, Health::Critical, NodeMode::Operational);
  carry(gps, fc, 1000000);
  CHECK(fc.status(kGpsId)->health == Health::Critical);
  CHECK(fc.alive(kGpsId, 3900000));
  CHECK_FALSE(fc.alive(kGpsId, 4100000));  // DroneCAN's offline timeout
}

TEST_CASE("the GPS's Fix2 decodes from the frames pydronecan makes for it") {
  // made with pydronecan (dronecan/pydronecan at 092d09cb) from the DSDL (dronecan/DSDL at
  // b4653c7a): latitude 42.3456789, longitude -71.12345678, from node 10, transfer ID 5
  const uint8_t frames[][8] = {
      {0xe9, 0x0e, 0x15, 0xcd, 0x5b, 0x07, 0x00, 0x85},
      {0x00, 0x00, 0xb1, 0x68, 0xde, 0x3a, 0x00, 0x25},
      {0x00, 0x00, 0x40, 0x00, 0x12, 0xb2, 0x37, 0x05},
      {0x12, 0x58, 0xf6, 0x93, 0x03, 0x37, 0xe0, 0x25},
      {0x0e, 0x4c, 0x00, 0x03, 0x75, 0x90, 0x00, 0x05},
      {0x00, 0x00, 0xc0, 0x3f, 0x00, 0x00, 0x80, 0x25},
      {0xbe, 0x00, 0x00, 0x00, 0x3e, 0x47, 0x10, 0x05},
      {0x43, 0x00, 0x38, 0x00, 0x34, 0x00, 0x44, 0x25},
  };
  const uint8_t last[3] = {0x00, 0x3d, 0x45};
  Node fc(kFlightControllerId);
  for (const auto& bytes : frames) {
    Frame f;
    f.id = 0x1804270a | CANARD_CAN_FRAME_EFF;
    std::copy(bytes, bytes + 8, f.data.begin());
    f.size = 8;
    fc.receive(f, 2000000);
  }
  CHECK(fc.fix() == nullptr);  // not until the last frame
  Frame f;
  f.id = 0x1804270a | CANARD_CAN_FRAME_EFF;
  std::copy(last, last + 3, f.data.begin());
  f.size = 3;
  fc.receive(f, 2000000);
  const Fix* fix = fc.fix();
  REQUIRE(fix != nullptr);
  CHECK(fix->timestamp_us == 123456789u);
  CHECK(fix->gnss_timestamp_us == 987654321u);
  CHECK(fix->leap_seconds == 18);
  CHECK(fix->latitude_deg == doctest::Approx(42.3456789).epsilon(1e-12));
  CHECK(fix->longitude_deg == doctest::Approx(-71.12345678).epsilon(1e-12));
  CHECK(fix->height_ellipsoid_m == doctest::Approx(12.345f));
  CHECK(fix->height_msl_m == doctest::Approx(45.678f));
  CHECK(fix->velocity.x == doctest::Approx(1.5f));
  CHECK(fix->velocity.y == doctest::Approx(-0.25f));
  CHECK(fix->velocity.z == doctest::Approx(0.125f));
  CHECK(fix->sats == 17);
  CHECK(fix->status == kFix3d);
  CHECK(fix->mode == 1);
  CHECK(fix->sub_mode == 1);
  REQUIRE(fix->covariance_count == 3);
  CHECK(fix->covariance[2] == doctest::Approx(4.0f));
  CHECK(fix->pdop == doctest::Approx(1.25f));
  CHECK(fc.fix_fresh(2500000));
  CHECK_FALSE(fc.fix_fresh(3500000));  // a GPS that stops talking for a second is stale
}
