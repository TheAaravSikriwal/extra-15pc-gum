// The ARK FPV's barometer, a Bosch BMP388 on I2C2. GPL-3.0.
//
// The registers, the trim's check and the oversampling follow PX4's driver for the same chip
// (src/drivers/barometer/bmp388, BSD-3-Clause, after Bosch's BMP3 Sensor API): pressure
// oversampled 16 times, temperature twice, no IIR filter. PX4 starts each reading by hand
// (forced mode); this one leaves the chip running on its own at 25 Hz (normal mode), since a
// reading at those settings takes about 37 ms.
//
// The compensation is the datasheet's floating-point form (BST-BMP388-DS001, its appendix):
// the 21 bytes of trim are scaled into coefficients once, then each reading is a polynomial in
// the raw temperature and pressure. The host tests check it against Bosch's integer form, the
// one PX4 runs; they agree to a hundredth of a pascal. The H743 has a double-precision FPU.
#pragma once

#include <cstddef>
#include <cstdint>
#include <utility>

#include "pcs14/h743/i2c.hpp"

namespace pcs14::bmp388 {

constexpr uint8_t kAddress = 0x76;  // 7-bit, SDO low, as PX4 starts it on the ARK FPV
namespace reg {
constexpr uint8_t CHIP_ID = 0x00, ERR = 0x02, STATUS = 0x03, DATA = 0x04;
constexpr uint8_t PWR_CTRL = 0x1B, OSR = 0x1C, ODR = 0x1D, CONFIG = 0x1F;
constexpr uint8_t TRIM_CRC = 0x30, CALIB = 0x31, CMD = 0x7E;
}  // namespace reg
constexpr uint8_t kChipId = 0x50, kChipId390 = 0x60;  // a BMP390 answers the same registers
constexpr uint8_t kSoftReset = 0xB6;
constexpr uint8_t kPwrNormal = 0x30 | 0x02 | 0x01;  // normal mode, temperature and pressure on
constexpr uint8_t kOsr = 0x04 | (0x01 << 3);       // pressure x16, temperature x2
constexpr uint8_t kOdr25Hz = 0x03;                  // 200 Hz / 2^3
constexpr uint8_t kIirOff = 0x00;
constexpr uint8_t kPressureReady = 0x20, kTemperatureReady = 0x40;  // STATUS's bits
constexpr size_t kTrimBytes = 21;

// the trim as stored (the datasheet's NVM_PAR_*), and as the compensation uses it (PAR_*)
struct Trim {
  uint16_t t1, t2;
  int8_t t3;
  int16_t p1, p2;
  int8_t p3, p4;
  uint16_t p5, p6;
  int8_t p7, p8;
  int16_t p9;
  int8_t p10, p11;
};
struct Coefficients {
  double t1, t2, t3, p1, p2, p3, p4, p5, p6, p7, p8, p9, p10, p11;
};

Trim parse_trim(const uint8_t* bytes);  // the 21 bytes from CALIB, little-endian
Coefficients coefficients(const Trim& trim);
// the trim's check: CRC-8 with polynomial 0x1D, from 0xFF, the result inverted (the catalogued
// CRC-8/SAE-J1850), against the byte at TRIM_CRC
uint8_t trim_crc(const uint8_t* bytes, size_t size);

struct Reading {
  double pressure_pa, temperature_c;
};
// raw 24-bit counts into pascals and degrees
Reading compensate(const Coefficients& c, uint32_t raw_temperature, uint32_t raw_pressure);

class Barometer {
 public:
  explicit Barometer(i2c::Device device) : device_(std::move(device)) {}
  // resets it, checks its id and its trim, and sets it running; false on any of those failing
  bool start(void (*wait_ms)(uint32_t) = nullptr);
  // true with `out` filled when a new reading is waiting
  bool read(Reading& out);
  uint32_t errors() const { return errors_; }

 private:
  i2c::Device device_;
  Coefficients c_{};
  uint32_t errors_ = 0;
};

}  // namespace pcs14::bmp388
