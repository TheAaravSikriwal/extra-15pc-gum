// The IMU driver against a fake IIM-42653: registers, the FIFO, the scales and the rotation.
#include <doctest/doctest.h>

#include <cmath>
#include <cstring>
#include <map>
#include <vector>

#include "pcs14/h743/iim42653.hpp"

using namespace pcs14;
using namespace pcs14::iim42653;
using doctest::Approx;

namespace {
// a register file and a FIFO, answering SPI the way the chip does: the first byte is the
// address (bit 7 set to read), then data in or out, with the address counting up on reads,
// except at FIFO_DATA, which streams the FIFO
struct FakeChip {
  std::map<uint8_t, uint8_t> regs{{reg::WHO_AM_I, kWhoAmI}};
  std::vector<uint8_t> fifo;
  std::vector<std::pair<uint8_t, uint8_t>> writes;

  Transfer bus() {
    return [this](const uint8_t* tx, uint8_t* rx, size_t n) {
      const uint8_t address = tx[0] & 0x7f;
      const bool read = tx[0] & 0x80;
      rx[0] = 0;
      if (!read) {
        regs[address] = tx[1];
        writes.push_back({address, tx[1]});
        return;
      }
      if (address == reg::FIFO_DATA) {
        for (size_t k = 1; k < n; ++k) {
          rx[k] = fifo.empty() ? 0xFF : fifo.front();
          if (!fifo.empty()) fifo.erase(fifo.begin());
        }
        return;
      }
      if (address == reg::FIFO_COUNTH) {
        regs[reg::FIFO_COUNTH] = static_cast<uint8_t>(fifo.size() >> 8);
        regs[reg::FIFO_COUNTH + 1] = static_cast<uint8_t>(fifo.size() & 0xff);
      }
      for (size_t k = 1; k < n; ++k) rx[k] = regs[static_cast<uint8_t>(address + k - 1)];
    };
  }
  // one packet: raw accel and gyro counts in the chip's own frame
  void push(int16_t ax, int16_t ay, int16_t az, int16_t gx, int16_t gy, int16_t gz) {
    const int16_t v[6] = {ax, ay, az, gx, gy, gz};
    fifo.push_back(0x68);  // accelerometer, gyro and timestamp
    for (int16_t x : v) {
      fifo.push_back(static_cast<uint8_t>(static_cast<uint16_t>(x) >> 8));
      fifo.push_back(static_cast<uint8_t>(x & 0xff));
    }
    fifo.push_back(0);  // 25 degrees
    fifo.push_back(0x12);
    fifo.push_back(0x34);
  }
};
}  // namespace

TEST_CASE("it starts: reset, the right WHO_AM_I, then the settings in order") {
  FakeChip chip;
  Imu imu(chip.bus(), [](uint32_t) {});
  REQUIRE(imu.start());
  // after the bank select and the reset come the settings, in order, then the FIFO flush
  REQUIRE(chip.writes.size() == 2 + kSetupCount + 1);
  CHECK(chip.writes[1] == std::make_pair(reg::DEVICE_CONFIG, uint8_t{0x01}));
  for (size_t k = 0; k < kSetupCount; ++k) {
    CHECK(chip.writes[2 + k].first == kSetup[k].address);
    CHECK(chip.writes[2 + k].second == kSetup[k].value);
  }
  CHECK(chip.regs[reg::PWR_MGMT0] == 0x0F);
}

TEST_CASE("a missing or wrong chip is turned away") {
  FakeChip chip;
  chip.regs[reg::WHO_AM_I] = 0x47;  // an ICM-42688-P
  Imu imu(chip.bus(), [](uint32_t) {});
  CHECK_FALSE(imu.start());
}

TEST_CASE("FIFO packets come out scaled and in the board's frame") {
  FakeChip chip;
  Imu imu(chip.bus(), [](uint32_t) {});
  REQUIRE(imu.start());
  // the chip feels 1 g along its own +z (2048 counts) and turns at 100 deg/s about its +x
  chip.push(0, 0, 2048, 1640, 0, 0);
  chip.push(0, 0, 2048, 1640, 0, 0);
  Sample s[4];
  REQUIRE(imu.read(s, 4) == 2);
  // roll 180 then yaw 270: the chip's z is the board's -z, its x the board's -y
  CHECK(s[0].accel.z == Approx(-kG).epsilon(0.001));
  CHECK(std::abs(s[0].accel.x) < 1e-3f);
  CHECK(s[0].gyro.y == Approx(-100.0f * kPi / 180).epsilon(0.01));
  CHECK(std::abs(s[0].gyro.x) < 1e-3f);
  CHECK(s[0].temperature_c == Approx(25.0f));
  CHECK(s[0].timestamp == 0x1234);
}

TEST_CASE("an empty FIFO's filler and 20-bit packets are refused") {
  uint8_t empty[kPacket];
  std::memset(empty, 0xFF, sizeof(empty));
  Sample s;
  CHECK_FALSE(parse(empty, s));
  uint8_t hires[kPacket] = {0x78};
  CHECK_FALSE(parse(hires, s));
}
