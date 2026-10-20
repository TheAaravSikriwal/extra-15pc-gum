// The ULog writer: the bytes it lays down, and a sample flight log for pyulog to read back
// (check_ulog.py, which ctest runs next when pyulog is there).
#include <doctest/doctest.h>

#include <cstdio>
#include <vector>

#include "pcs14/log_topics.hpp"
#include "pcs14/ulog.hpp"

using namespace pcs14;

namespace {
struct Buffer {
  std::vector<uint8_t> bytes;
  ULogWriter::Sink sink() {
    return [this](const uint8_t* d, size_t n) { bytes.insert(bytes.end(), d, d + n); };
  }
};
uint16_t u16(const std::vector<uint8_t>& b, size_t at) {
  return static_cast<uint16_t>(b[at] | (b[at + 1] << 8));
}
}  // namespace

TEST_CASE("the header, then the flag bits, then each message framed by its size and type") {
  Buffer buffer;
  ULogWriter log(buffer.sink());
  log.begin(1234);
  const auto& b = buffer.bytes;
  REQUIRE(b.size() == 16 + 3 + 40);
  CHECK(std::string(b.begin(), b.begin() + 4) == "ULog");
  CHECK(b[4] == 0x01);
  CHECK(b[5] == 0x12);
  CHECK(b[6] == 0x35);
  CHECK(b[7] == 1);  // version 1
  CHECK(b[8] == 0xd2);  // 1234 = 0x04d2, little-endian
  CHECK(b[9] == 0x04);
  CHECK(u16(b, 16) == 40);
  CHECK(b[18] == 'B');

  const size_t before = b.size();
  log.format("x:uint64_t timestamp;float y;");
  CHECK(u16(b, before) == 29);
  CHECK(b[before + 2] == 'F');
  const size_t sub = b.size();
  CHECK(log.subscribe("x") == 0);
  CHECK(log.subscribe("x", 1) == 1);
  CHECK(b[sub + 2] == 'A');
  CHECK(b[sub + 3] == 0);  // instance
  CHECK(u16(b, sub + 4) == 0);  // id
}

TEST_CASE("a sample's fields go in order, packed") {
  Packer p;
  p.put(static_cast<uint64_t>(7)).put(1.5f).put_bool(true).put(static_cast<uint8_t>(3));
  CHECK(p.size() == 8 + 4 + 1 + 1);
  CHECK(p.data()[0] == 7);
  CHECK(p.data()[12] == 1);
  CHECK(p.data()[13] == 3);
}

// The sample flight check_ulog.py reads: two seconds at 10 Hz of every topic, with values
// worked out from the sample's index so the check can recompute them.
TEST_CASE("write a sample flight log for pyulog") {
  std::FILE* file = std::fopen("ulog_sample.ulg", "wb");
  REQUIRE(file != nullptr);
  ULogWriter out([file](const uint8_t* d, size_t n) { std::fwrite(d, 1, n, file); });
  out.begin(0);
  out.info("sys_name", "pcs14");
  out.parameter("MC_ROLL_P", 9.0f);
  out.parameter("CA_ROTOR_COUNT", static_cast<int32_t>(4));
  FlightLogWriter log(out, true);
  for (int k = 0; k < 20; ++k) {
    const uint64_t t = 100000u * static_cast<uint64_t>(k + 1);
    const float f = static_cast<float>(k);
    log.log(TruthPosition{t, {f, 2 * f, -0.5f * f}, {1, 2, -0.5f}});
    log.log(TruthAttitude{t, Quat::from_euler(0, 0, 0.1f * f)});
    log.log(EscSample{t, {500 + f, 501 + f, 502 + f, 503 + f}});
    log.log(ImuLog{t, {0.01f * f, 0, 0}, {0, 0, -kG}});
    log.log(StatusLog{t, k < 5 ? kArmingStandby : kArmingArmed, kNavAcro});
    log.log(LandLog{t, k < 8});
    FailsafeLog flags{t};
    flags.link_lost = k >= 15;
    flags.battery_warning = k >= 18 ? 1 : 0;
    flags.geofence_breached = k >= 12;
    log.log(flags);
    log.log(BatteryLog{t, 24.0f - 0.1f * f, 20.0f, 1.0f - 0.01f * f});
  }
  out.text(6, 2000000, "sample done");
  std::fclose(file);
}
