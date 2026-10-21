// DroneCAN on the ARK FPV's CAN bus: the GPS (in V) and the CAN nodes in the modules. GPL-3.0.
//
// The transport (frames, transfers, transfer IDs, reassembly) is libcanard, DroneCAN's own
// fork (MIT). This layer is a node on top of it: it sends its NodeStatus once a second, the
// heartbeat every DroneCAN node owes the bus, and keeps track of every other node's, so the
// flight controller knows the GPS and the module nodes are there and healthy. A node that has
// said nothing for 3 s is offline, as the spec has it.
//
// Next: the GPS's own messages (uavcan.equipment.gnss.Fix2 and the compass and barometer on the
// same board). They're multi-frame, and their transfer CRC starts from each type's signature,
// which comes from the DSDL compiler; until that's in, only NodeStatus is decoded.
#pragma once

#include <array>
#include <cstddef>
#include <cstdint>

extern "C" {
#include "canard.h"
}

namespace pcs14::dronecan {

constexpr uint16_t kNodeStatusId = 341;  // uavcan.protocol.NodeStatus
// its signature, as libcanard's original demo had it; a single-frame transfer like this one
// carries no CRC, so it never reaches the wire
constexpr uint64_t kNodeStatusSignature = 0x0f0868d0c1a7c6f1ULL;
constexpr size_t kNodeStatusBytes = 7;
constexpr uint64_t kStatusEveryUs = 1000000;
constexpr uint64_t kOfflineUs = 3000000;
constexpr uint8_t kFlightControllerId = 1;  // the bus's node IDs, as the build assigns them
constexpr uint8_t kGpsId = 10;

enum class Health : uint8_t { Ok = 0, Warning = 1, Error = 2, Critical = 3 };
enum class NodeMode : uint8_t {
  Operational = 0,
  Initialization = 1,
  Maintenance = 2,
  SoftwareUpdate = 3,
  Offline = 7
};

struct NodeStatus {
  uint32_t uptime_s = 0;
  Health health = Health::Ok;
  NodeMode mode = NodeMode::Operational;
  uint8_t sub_mode = 0;
  uint16_t vendor_code = 0;
};

void encode(const NodeStatus& s, uint8_t* out);  // kNodeStatusBytes
NodeStatus decode_node_status(const uint8_t* bytes, size_t size);

struct Frame {
  uint32_t id = 0;  // 29 bits, with libcanard's extended-frame flag
  std::array<uint8_t, 8> data{};
  uint8_t size = 0;
};

class Node {
 public:
  explicit Node(uint8_t node_id);
  Node(const Node&) = delete;
  Node& operator=(const Node&) = delete;

  // a frame off the bus
  void receive(const Frame& f, uint64_t now_us);
  // the next frame to put on the bus; false when there's none
  bool next_frame(Frame& out);
  // every pass of the loop: its own NodeStatus once a second, and the stale transfers cleared
  void update(uint64_t now_us, Health health, NodeMode mode);

  bool alive(uint8_t node_id, uint64_t now_us) const;
  const NodeStatus* status(uint8_t node_id) const;  // the last one heard, or nullptr

  // libcanard's callbacks, routed here through its user pointer
  void on_transfer(CanardRxTransfer* t);

 private:
  struct Heard {
    bool ever = false;
    uint64_t at_us = 0;
    NodeStatus status;
  };
  CanardInstance canard_{};
  alignas(8) uint8_t arena_[4096]{};
  uint8_t status_transfer_id_ = 0;
  uint64_t started_us_ = 0, next_status_us_ = 0, last_cleanup_us_ = 0;
  bool started_ = false;
  uint64_t now_us_ = 0;
  std::array<Heard, 128> heard_{};
};

}  // namespace pcs14::dronecan
