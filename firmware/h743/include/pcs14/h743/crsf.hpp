// CRSF, the protocol the ExpressLRS receiver speaks on the ARK FPV's RC port (USART6, 420000
// baud, 8N1). GPL-3.0.
//
// A frame is [address][length][type][payload][crc]: the length counts the type, the payload and
// the CRC, and the CRC is CRC-8/DVB-S2 (polynomial 0xD5) over the type and payload. The RC
// channels frame (type 0x16) packs 16 channels of 11 bits each, least significant bit first,
// 172 to 1811 for 988 to 2012 us. ExpressLRS's own documentation of the protocol is the
// reference (expresslrs.org, and the CRSF specification it links).
#pragma once

#include <array>
#include <cstddef>
#include <cstdint>

namespace pcs14::crsf {

constexpr uint8_t kAddressFlightController = 0xC8;
constexpr uint8_t kTypeLinkStatistics = 0x14;
constexpr uint8_t kTypeRcChannels = 0x16;
constexpr size_t kMaxFrame = 64;
constexpr uint16_t kChannelMin = 172, kChannelMid = 992, kChannelMax = 1811;

uint8_t crc8(const uint8_t* data, size_t size);

struct Channels {
  std::array<uint16_t, 16> raw{};  // 172 to 1811
  // a channel from -1 to 1 (sticks), centered at 992
  float stick(size_t k) const;
  // a channel from 0 to 1 (the throttle)
  float unit(size_t k) const;
  // a switch: on above the middle
  bool on(size_t k) const { return raw[k] > kChannelMid + 200; }
};

struct LinkStatistics {
  uint8_t uplink_rssi_1, uplink_rssi_2, uplink_quality;  // RSSI as -dBm, quality in %
  int8_t uplink_snr;
  uint8_t active_antenna, rf_mode, tx_power;
  uint8_t downlink_rssi, downlink_quality;
  int8_t downlink_snr;
};

// reads bytes as they come off the UART and hands out whole, checked frames
class Parser {
 public:
  // one byte; true when it completed a frame with a good CRC
  bool push(uint8_t byte);
  uint8_t type() const { return buffer_[2]; }
  const uint8_t* payload() const { return buffer_ + 3; }
  size_t payload_size() const { return length_ - 2; }
  bool channels(Channels& out) const;
  bool link(LinkStatistics& out) const;
  uint32_t bad_crc() const { return bad_crc_; }

 private:
  uint8_t buffer_[kMaxFrame]{};
  size_t have_ = 0, length_ = 0;
  uint32_t bad_crc_ = 0;
};

// packs channels into an RC channels frame, as a receiver would (for the tests, and for a
// ground station that speaks CRSF)
size_t pack_channels(const Channels& ch, uint8_t* out);

}  // namespace pcs14::crsf
