// The compass and barometer drivers against fake chips on a fake I2C bus.
#include <doctest/doctest.h>

#include <cmath>
#include <cstdint>
#include <cstring>
#include <map>
#include <vector>

#include "pcs14/h743/bmp388.hpp"
#include "pcs14/h743/iis2mdc.hpp"

using namespace pcs14;
using doctest::Approx;

namespace {
// a register file that counts its address up on reads, and remembers every write
struct FakeChip {
  std::map<uint8_t, uint8_t> regs;
  std::vector<std::pair<uint8_t, uint8_t>> writes;
  bool present = true;

  i2c::Device device() {
    return {[this](uint8_t reg, uint8_t* out, size_t n) {
              if (!present) return false;
              for (size_t k = 0; k < n; ++k) out[k] = regs[static_cast<uint8_t>(reg + k)];
              return true;
            },
            [this](uint8_t reg, uint8_t value) {
              if (!present) return false;
              regs[reg] = value;
              writes.push_back({reg, value});
              return true;
            }};
  }
  void put(uint8_t reg, const std::vector<uint8_t>& bytes) {
    for (size_t k = 0; k < bytes.size(); ++k) regs[static_cast<uint8_t>(reg + k)] = bytes[k];
  }
};

std::vector<uint8_t> le16(int v) {
  return {static_cast<uint8_t>(v & 0xFF), static_cast<uint8_t>((v >> 8) & 0xFF)};
}
}  // namespace

TEST_CASE("the compass starts the way PX4's driver does, and reads x, y and minus z") {
  FakeChip chip;
  chip.regs[iis2mdc::reg::WHO_AM_I] = iis2mdc::kWhoAmI;
  iis2mdc::Compass compass(chip.device());
  REQUIRE(compass.start());
  const std::vector<std::pair<uint8_t, uint8_t>> want{
      {0x60, 0x8C}, {0x61, 0x02}, {0x62, 0x10}};  // PX4's iis2mdc init
  CHECK(chip.writes == want);

  iis2mdc::Sample s{};
  CHECK_FALSE(compass.read(s));  // nothing new yet
  chip.regs[iis2mdc::reg::STATUS] = iis2mdc::kNewXyz;
  std::vector<uint8_t> bytes;
  for (int v : {144, -10, 287, 40}) {  // 0.216, -0.015, 0.4305 gauss; 30 degrees
    const std::vector<uint8_t> w = le16(v);
    bytes.insert(bytes.end(), w.begin(), w.end());
  }
  chip.put(iis2mdc::reg::OUTX_L, bytes);
  REQUIRE(compass.read(s));
  CHECK(s.field.x == Approx(0.216f));
  CHECK(s.field.y == Approx(-0.015f));
  CHECK(s.field.z == Approx(-0.4305f));  // the chip's z is up
  CHECK(s.temperature_c == Approx(30.0f));
}

TEST_CASE("a compass that isn't there, or isn't an IIS2MDC, doesn't start") {
  FakeChip chip;
  chip.regs[iis2mdc::reg::WHO_AM_I] = 0x3D;  // some other chip
  CHECK_FALSE(iis2mdc::Compass(chip.device()).start());
  chip.present = false;
  CHECK_FALSE(iis2mdc::Compass(chip.device()).start());
}

TEST_CASE("the barometer's trim check is CRC-8/SAE-J1850") {
  const char* check = "123456789";  // the CRC catalogue's check string
  CHECK(bmp388::trim_crc(reinterpret_cast<const uint8_t*>(check), 9) == 0x4B);
}

namespace {
// Bosch's integer compensation, as PX4's bmp388 driver carries it, the reference the
// floating-point form is checked against. From Bosch Sensortec's BMP3 Sensor API
// (github.com/BoschSensortec/BMP3-Sensor-API, bmp3.c):
//   Copyright (c) 2020 Bosch Sensortec GmbH. All rights reserved.
//   BSD-3-Clause. Redistribution and use in source and binary forms, with or without
//   modification, are permitted provided that the following conditions are met:
//   1. Redistributions of source code must retain the above copyright notice, this list of
//   conditions and the following disclaimer. 2. Redistributions in binary form must
//   reproduce the above copyright notice, this list of conditions and the following
//   disclaimer in the documentation and/or other materials provided with the distribution.
//   3. Neither the name of the copyright holder nor the names of its contributors may be
//   used to endorse or promote products derived from this software without specific prior
//   written permission. THIS SOFTWARE IS PROVIDED BY THE COPYRIGHT HOLDERS AND CONTRIBUTORS
//   "AS IS" AND ANY EXPRESS OR IMPLIED WARRANTIES, INCLUDING, BUT NOT LIMITED TO, THE
//   IMPLIED WARRANTIES OF MERCHANTABILITY AND FITNESS FOR A PARTICULAR PURPOSE ARE
//   DISCLAIMED. IN NO EVENT SHALL THE COPYRIGHT HOLDER OR CONTRIBUTORS BE LIABLE FOR ANY
//   DIRECT, INDIRECT, INCIDENTAL, SPECIAL, EXEMPLARY, OR CONSEQUENTIAL DAMAGES (INCLUDING,
//   BUT NOT LIMITED TO, PROCUREMENT OF SUBSTITUTE GOODS OR SERVICES; LOSS OF USE, DATA, OR
//   PROFITS; OR BUSINESS INTERRUPTION) HOWEVER CAUSED AND ON ANY THEORY OF LIABILITY,
//   WHETHER IN CONTRACT, STRICT LIABILITY, OR TORT (INCLUDING NEGLIGENCE OR OTHERWISE)
//   ARISING IN ANY WAY OUT OF THE USE OF THIS SOFTWARE, EVEN IF ADVISED OF THE POSSIBILITY
//   OF SUCH DAMAGE.
void bosch_integer(const bmp388::Trim& c, int64_t ut, int64_t up, double& t, double& p) {
  int64_t pd1 = ut - 256 * static_cast<int64_t>(c.t1);
  int64_t pd2 = c.t2 * pd1;
  int64_t pd3 = pd1 * pd1;
  int64_t pd4 = pd3 * c.t3;
  int64_t pd5 = pd2 * 262144 + pd4;
  const int64_t t_lin = pd5 / 4294967296;
  t = static_cast<double>((t_lin * 25) / 16384) / 100;
  pd1 = t_lin * t_lin;
  pd2 = pd1 / 64;
  pd3 = (pd2 * t_lin) / 256;
  pd4 = (c.p8 * pd3) / 32;
  pd5 = (c.p7 * pd1) * 16;
  int64_t pd6 = (c.p6 * t_lin) * 4194304;
  const int64_t offset = (c.p5 * 140737488355328) + pd4 + pd5 + pd6;
  pd2 = (c.p4 * pd3) / 32;
  pd4 = (c.p3 * pd1) * 4;
  pd5 = (c.p2 - 16384) * t_lin * 2097152;
  const int64_t sensitivity = ((c.p1 - 16384) * 70368744177664) + pd2 + pd4 + pd5;
  pd1 = (sensitivity / 16777216) * up;
  pd2 = c.p10 * t_lin;
  pd3 = pd2 + (65536 * c.p9);
  pd4 = (pd3 * up) / 8192;
  pd5 = (up * (pd4 / 10)) / 512;
  pd5 = pd5 * 10;
  pd6 = static_cast<int64_t>(static_cast<uint64_t>(up) * static_cast<uint64_t>(up));
  pd2 = (c.p11 * pd6) / 65536;
  pd3 = (pd2 * up) / 128;
  pd4 = (offset / 4) + pd1 + pd5 + pd3;
  p = static_cast<double>((static_cast<uint64_t>(pd4) * 25) / 1099511627776ull) / 100;
}

// made-up trim, not a real chip's, picked so the raw counts below land on ordinary weather
std::vector<uint8_t> trim_bytes() {
  std::vector<uint8_t> b;
  auto add16 = [&](int v) {
    b.push_back(static_cast<uint8_t>(v & 0xFF));
    b.push_back(static_cast<uint8_t>((v >> 8) & 0xFF));
  };
  auto add8 = [&](int v) { b.push_back(static_cast<uint8_t>(v & 0xFF)); };
  add16(27500), add16(19000), add8(-10);         // t1, t2, t3
  add16(-1500), add16(-2500), add8(30), add8(-5);  // p1 to p4
  add16(25000), add16(30000), add8(-10), add8(-5);  // p5 to p8
  add16(15000), add8(10), add8(-60);              // p9 to p11
  return b;
}
}  // namespace

TEST_CASE("the trim parses, and the datasheet's floating point matches Bosch's integers") {
  const std::vector<uint8_t> raw = trim_bytes();
  REQUIRE(raw.size() == bmp388::kTrimBytes);
  const bmp388::Trim trim = bmp388::parse_trim(raw.data());
  CHECK(trim.t1 == 27500);
  CHECK(trim.p1 == -1500);
  CHECK(trim.p6 == 30000);
  CHECK(trim.p11 == -60);
  const bmp388::Coefficients c = bmp388::coefficients(trim);
  for (const auto& [ut, up] : {std::pair<uint32_t, uint32_t>{8000000, 6600000},
                               {8300000, 6400000}, {7600000, 7000000}}) {
    const bmp388::Reading r = bmp388::compensate(c, ut, up);
    double t = 0, p = 0;
    bosch_integer(trim, ut, up, t, p);
    CHECK(r.temperature_c == Approx(t).epsilon(0.001));
    CHECK(std::abs(r.pressure_pa - p) < 0.05);  // a twentieth of a pascal: 4 mm of height
    CHECK(r.pressure_pa > 80000);
    CHECK(r.pressure_pa < 105000);
  }
}

TEST_CASE("the barometer checks its id and trim, sets PX4's oversampling, and reads") {
  FakeChip chip;
  chip.regs[bmp388::reg::CHIP_ID] = bmp388::kChipId;
  const std::vector<uint8_t> raw = trim_bytes();
  chip.put(bmp388::reg::CALIB, raw);
  chip.regs[bmp388::reg::TRIM_CRC] = bmp388::trim_crc(raw.data(), raw.size());
  bmp388::Barometer baro(chip.device());
  REQUIRE(baro.start());
  const std::vector<std::pair<uint8_t, uint8_t>> want{
      {0x7E, 0xB6}, {0x1C, 0x0C}, {0x1D, 0x03}, {0x1F, 0x00}, {0x1B, 0x33}};
  CHECK(chip.writes == want);

  bmp388::Reading r{};
  CHECK_FALSE(baro.read(r));  // no data ready
  // 8300000 temperature counts, 6400000 pressure counts, little-endian after the status
  chip.put(bmp388::reg::STATUS, {0x70, 0x00, 0xA8, 0x61, 0xE0, 0xA5, 0x7E});
  REQUIRE(baro.read(r));
  CHECK(r.temperature_c == Approx(22.239).epsilon(0.001));
  CHECK(r.pressure_pa == Approx(98050.42).epsilon(1e-6));

  chip.regs[bmp388::reg::TRIM_CRC] ^= 1;  // a corrupt trim
  CHECK_FALSE(bmp388::Barometer(chip.device()).start());
}
