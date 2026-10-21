// DroneCAN on the ARK FPV's CAN bus: two nodes, both libcanard, talking frame by frame.
#include <doctest/doctest.h>

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
