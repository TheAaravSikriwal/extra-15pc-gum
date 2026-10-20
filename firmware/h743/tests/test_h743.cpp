// The ARK FPV layer's logic on the host: CRSF from the receiver, DShot to the ESC.
#include <doctest/doctest.h>

#include <cstring>

#include "pcs14/h743/crsf.hpp"
#include "pcs14/h743/dshot.hpp"
#include "pcs14/monitor.hpp"

using namespace pcs14;

TEST_CASE("CRC-8/DVB-S2: the standard check value") {
  const char* check = "123456789";
  CHECK(crsf::crc8(reinterpret_cast<const uint8_t*>(check), 9) == 0xBC);
}

TEST_CASE("RC channels come through a packed frame and back") {
  crsf::Channels sent;
  for (size_t k = 0; k < 16; ++k) sent.raw[k] = static_cast<uint16_t>(172 + k * 100);
  sent.raw[2] = crsf::kChannelMid;
  uint8_t frame[crsf::kMaxFrame];
  const size_t n = crsf::pack_channels(sent, frame);
  CHECK(n == 26);
  crsf::Parser parser;
  bool done = false;
  for (size_t k = 0; k < n; ++k) done = parser.push(frame[k]);
  REQUIRE(done);
  crsf::Channels got;
  REQUIRE(parser.channels(got));
  CHECK(got.raw == sent.raw);
  CHECK(got.stick(2) == doctest::Approx(0.0f));
  CHECK(got.unit(0) == doctest::Approx(0.0f));
}

TEST_CASE("a corrupted frame is dropped and counted, and the next good one still reads") {
  crsf::Channels sent;
  sent.raw.fill(crsf::kChannelMid);
  uint8_t frame[crsf::kMaxFrame];
  const size_t n = crsf::pack_channels(sent, frame);
  crsf::Parser parser;
  frame[10] ^= 0x40;
  bool done = false;
  for (size_t k = 0; k < n; ++k) done = parser.push(frame[k]);
  CHECK_FALSE(done);
  CHECK(parser.bad_crc() == 1);
  frame[10] ^= 0x40;
  parser.push(0x55);  // noise between frames is skipped
  for (size_t k = 0; k < n; ++k) done = parser.push(frame[k]);
  CHECK(done);
}

TEST_CASE("the sticks and switches read off the channels") {
  crsf::Channels ch;
  ch.raw[0] = crsf::kChannelMax;
  ch.raw[1] = crsf::kChannelMin;
  ch.raw[4] = 1800;
  ch.raw[5] = 200;
  CHECK(ch.stick(0) == doctest::Approx(1.0f));
  CHECK(ch.stick(1) == doctest::Approx(-1.0f).epsilon(0.01));
  CHECK(ch.on(4));
  CHECK_FALSE(ch.on(5));
}

TEST_CASE("DShot600 from a 240 MHz timer: 400 counts a bit, 300 high for a 1, 150 for a 0") {
  const dshot::Timing t = dshot::timing(240000000, 600000);
  CHECK(t.period == 400);
  CHECK(t.one == 300);
  CHECK(t.zero == 150);
  const dshot::Buffer b = dshot::encode(dshot_frame(1046), t);  // 0x82c6
  CHECK(b[0] == 300);   // 1
  CHECK(b[1] == 150);   // 0
  CHECK(b[6] == 300);   // 0x82c6 = 1000 0010 1100 0110
  CHECK(b[15] == 150);
  CHECK(b[16] == 0);    // then the line rests low
  CHECK(b[17] == 0);
}

TEST_CASE("throttle: idle at 48, full at 2047, and 0 kept for stop") {
  CHECK(dshot::throttle_value(0) == 48);
  CHECK(dshot::throttle_value(1) == 2047);
  CHECK(dshot::throttle_value(0.5f) == 1048);
  CHECK(kDshotStop == 0);
}
