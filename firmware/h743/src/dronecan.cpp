// DroneCAN: a node on libcanard. GPL-3.0.
#include "pcs14/h743/dronecan.hpp"

#include <cstring>

namespace pcs14::dronecan {

namespace {
bool should_accept(const CanardInstance*, uint64_t* signature, uint16_t data_type_id,
                   CanardTransferType type, uint8_t) {
  if (type != CanardTransferTypeBroadcast) return false;
  if (data_type_id == kNodeStatusId) {
    *signature = kNodeStatusSignature;
  } else if (data_type_id == kFix2Id) {
    *signature = kFix2Signature;
  } else {
    return false;  // everything else waits for its decoder
  }
  return true;
}

void on_reception(CanardInstance* ins, CanardRxTransfer* transfer) {
  static_cast<Node*>(canardGetUserReference(ins))->on_transfer(transfer);
}
}  // namespace

void encode(const NodeStatus& s, uint8_t* out) {
  std::memset(out, 0, kNodeStatusBytes);
  const uint8_t health = static_cast<uint8_t>(s.health), mode = static_cast<uint8_t>(s.mode);
  canardEncodeScalar(out, 0, 32, &s.uptime_s);
  canardEncodeScalar(out, 32, 2, &health);
  canardEncodeScalar(out, 34, 3, &mode);
  canardEncodeScalar(out, 37, 3, &s.sub_mode);
  canardEncodeScalar(out, 40, 16, &s.vendor_code);
}

NodeStatus decode_node_status(const uint8_t* bytes, size_t size) {
  // libcanard decodes from a transfer; a single frame's payload is a transfer of its own
  CanardRxTransfer t{};
  t.payload_head = bytes;
  t.payload_len = static_cast<uint16_t>(size);
  NodeStatus s;
  uint8_t health = 0, mode = 0;
  canardDecodeScalar(&t, 0, 32, false, &s.uptime_s);
  canardDecodeScalar(&t, 32, 2, false, &health);
  canardDecodeScalar(&t, 34, 3, false, &mode);
  canardDecodeScalar(&t, 37, 3, false, &s.sub_mode);
  canardDecodeScalar(&t, 40, 16, false, &s.vendor_code);
  s.health = static_cast<Health>(health);
  s.mode = static_cast<NodeMode>(mode);
  return s;
}

bool decode_fix2(const CanardRxTransfer* t, Fix& out) {
  // the DSDL's layout, in bits: two uint56 timestamps, uint3 time standard, void13, uint8 leap
  // seconds, int37 longitude and latitude (1e-8 degrees), int27 heights (mm), float32[3]
  // velocity, uint6 sats, uint2 status, uint4 mode, uint6 sub mode, then float16[<=36]
  // covariance with a 6-bit length, float16 pdop, and an ECEF tail this doesn't need
  constexpr uint32_t kFixedBits = 384;
  if (t->payload_len * 8u < kFixedBits + 6) return false;
  Fix f;
  int64_t lon = 0, lat = 0;
  int32_t h_ellipsoid = 0, h_msl = 0;
  float v[3] = {};
  canardDecodeScalar(t, 0, 56, false, &f.timestamp_us);
  canardDecodeScalar(t, 56, 56, false, &f.gnss_timestamp_us);
  canardDecodeScalar(t, 112, 3, false, &f.time_standard);
  canardDecodeScalar(t, 128, 8, false, &f.leap_seconds);
  canardDecodeScalar(t, 136, 37, true, &lon);
  canardDecodeScalar(t, 173, 37, true, &lat);
  canardDecodeScalar(t, 210, 27, true, &h_ellipsoid);
  canardDecodeScalar(t, 237, 27, true, &h_msl);
  for (uint32_t k = 0; k < 3; ++k) canardDecodeScalar(t, 264 + 32 * k, 32, true, &v[k]);
  canardDecodeScalar(t, 360, 6, false, &f.sats);
  canardDecodeScalar(t, 366, 2, false, &f.status);
  canardDecodeScalar(t, 368, 4, false, &f.mode);
  canardDecodeScalar(t, 372, 6, false, &f.sub_mode);
  uint8_t n = 0;
  canardDecodeScalar(t, 378, 6, false, &n);
  if (n > 36 || t->payload_len * 8u < kFixedBits + 16u * (n + 1u)) return false;
  for (uint32_t k = 0; k < n; ++k) {
    uint16_t half = 0;
    canardDecodeScalar(t, kFixedBits + 16 * k, 16, false, &half);
    f.covariance[k] = canardConvertFloat16ToNativeFloat(half);
  }
  f.covariance_count = n;
  uint16_t pdop = 0;
  canardDecodeScalar(t, kFixedBits + 16u * n, 16, false, &pdop);
  f.pdop = canardConvertFloat16ToNativeFloat(pdop);
  f.longitude_deg = static_cast<double>(lon) * 1e-8;
  f.latitude_deg = static_cast<double>(lat) * 1e-8;
  f.height_ellipsoid_m = static_cast<float>(h_ellipsoid) * 0.001f;
  f.height_msl_m = static_cast<float>(h_msl) * 0.001f;
  f.velocity = {v[0], v[1], v[2]};
  out = f;
  return true;
}

Node::Node(uint8_t node_id) {
  canardInit(&canard_, arena_, sizeof(arena_), on_reception, should_accept, this);
  canardSetLocalNodeID(&canard_, node_id);
}

void Node::on_transfer(CanardRxTransfer* t) {
  if (t->data_type_id == kFix2Id) {
    if (decode_fix2(t, fix_)) {
      have_fix_ = true;
      fix_at_us_ = now_us_;
    }
    return;
  }
  if (t->data_type_id != kNodeStatusId || t->payload_len < kNodeStatusBytes) return;
  uint8_t bytes[kNodeStatusBytes];
  for (size_t k = 0; k < kNodeStatusBytes; ++k) {
    uint8_t b = 0;
    canardDecodeScalar(t, static_cast<uint32_t>(8 * k), 8, false, &b);
    bytes[k] = b;
  }
  Heard& h = heard_[t->source_node_id & 0x7F];
  h.ever = true;
  h.at_us = now_us_;
  h.status = decode_node_status(bytes, kNodeStatusBytes);
}

void Node::receive(const Frame& f, uint64_t now_us) {
  now_us_ = now_us;
  CanardCANFrame frame{};
  frame.id = f.id;
  std::memcpy(frame.data, f.data.data(), f.size);
  frame.data_len = f.size;
  canardHandleRxFrame(&canard_, &frame, now_us);
}

bool Node::next_frame(Frame& out) {
  const CanardCANFrame* f = canardPeekTxQueue(&canard_);
  if (f == nullptr) return false;
  out.id = f->id;
  out.size = f->data_len;
  std::memcpy(out.data.data(), f->data, f->data_len);
  canardPopTxQueue(&canard_);
  return true;
}

void Node::update(uint64_t now_us, Health health, NodeMode mode) {
  now_us_ = now_us;
  if (!started_) {
    started_ = true;
    started_us_ = next_status_us_ = last_cleanup_us_ = now_us;
  }
  if (now_us >= next_status_us_) {
    next_status_us_ += kStatusEveryUs;
    NodeStatus s;
    s.uptime_s = static_cast<uint32_t>((now_us - started_us_) / 1000000);
    s.health = health;
    s.mode = mode;
    uint8_t bytes[kNodeStatusBytes];
    encode(s, bytes);
    canardBroadcast(&canard_, kNodeStatusSignature, kNodeStatusId, &status_transfer_id_,
                    CANARD_TRANSFER_PRIORITY_LOW, bytes, kNodeStatusBytes);
  }
  if (now_us - last_cleanup_us_ >= CANARD_RECOMMENDED_STALE_TRANSFER_CLEANUP_INTERVAL_USEC) {
    canardCleanupStaleTransfers(&canard_, now_us);
    last_cleanup_us_ = now_us;
  }
}

bool Node::alive(uint8_t node_id, uint64_t now_us) const {
  const Heard& h = heard_[node_id & 0x7F];
  return h.ever && now_us - h.at_us <= kOfflineUs;
}

const NodeStatus* Node::status(uint8_t node_id) const {
  const Heard& h = heard_[node_id & 0x7F];
  return h.ever ? &h.status : nullptr;
}

}  // namespace pcs14::dronecan
