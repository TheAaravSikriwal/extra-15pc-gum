// CRSF. GPL-3.0.
#include "pcs14/h743/crsf.hpp"

namespace pcs14::crsf {

uint8_t crc8(const uint8_t* data, size_t size) {
  uint8_t crc = 0;
  for (size_t k = 0; k < size; ++k) {
    crc ^= data[k];
    for (int bit = 0; bit < 8; ++bit)
      crc = static_cast<uint8_t>((crc & 0x80) ? (crc << 1) ^ 0xD5 : crc << 1);
  }
  return crc;
}

float Channels::stick(size_t k) const {
  const float v = (static_cast<float>(raw[k]) - kChannelMid) / (kChannelMax - kChannelMid);
  return v < -1 ? -1 : (v > 1 ? 1 : v);
}

float Channels::unit(size_t k) const {
  const float v = static_cast<float>(raw[k] - kChannelMin) /
                  static_cast<float>(kChannelMax - kChannelMin);
  return raw[k] < kChannelMin ? 0 : (v > 1 ? 1 : v);
}

bool Parser::push(uint8_t byte) {
  if (have_ == 0) {
    // a frame starts with an address; the flight controller's is the one receivers use, and
    // some send 0xEE (the transmitter's) or 0xEA (the radio's) too
    if (byte != kAddressFlightController && byte != 0xEE && byte != 0xEA) return false;
    buffer_[have_++] = byte;
    return false;
  }
  if (have_ == 1) {
    if (byte < 2 || byte > kMaxFrame - 2) {  // not a length a frame can have: start over
      have_ = 0;
      return false;
    }
    length_ = byte;
    buffer_[have_++] = byte;
    return false;
  }
  buffer_[have_++] = byte;
  if (have_ < length_ + 2) return false;
  have_ = 0;
  if (crc8(buffer_ + 2, length_ - 1) != buffer_[length_ + 1]) {
    ++bad_crc_;
    return false;
  }
  return true;
}

bool Parser::channels(Channels& out) const {
  if (type() != kTypeRcChannels || payload_size() < 22) return false;
  const uint8_t* p = payload();
  uint32_t bits = 0;
  int count = 0;
  size_t k = 0;
  for (size_t i = 0; i < 22 && k < 16; ++i) {
    bits |= static_cast<uint32_t>(p[i]) << count;
    count += 8;
    while (count >= 11 && k < 16) {
      out.raw[k++] = static_cast<uint16_t>(bits & 0x7ff);
      bits >>= 11;
      count -= 11;
    }
  }
  return true;
}

bool Parser::link(LinkStatistics& out) const {
  if (type() != kTypeLinkStatistics || payload_size() < 10) return false;
  const uint8_t* p = payload();
  out = {p[0], p[1], p[2], static_cast<int8_t>(p[3]), p[4], p[5], p[6],
         p[7], p[8], static_cast<int8_t>(p[9])};
  return true;
}

size_t pack_channels(const Channels& ch, uint8_t* out) {
  out[0] = kAddressFlightController;
  out[1] = 24;  // type, 22 bytes of channels, CRC
  out[2] = kTypeRcChannels;
  uint32_t bits = 0;
  int count = 0;
  size_t i = 3;
  for (uint16_t v : ch.raw) {
    bits |= static_cast<uint32_t>(v & 0x7ff) << count;
    count += 11;
    while (count >= 8) {
      out[i++] = static_cast<uint8_t>(bits & 0xff);
      bits >>= 8;
      count -= 8;
    }
  }
  out[i] = crc8(out + 2, 23);
  return i + 1;
}

}  // namespace pcs14::crsf
