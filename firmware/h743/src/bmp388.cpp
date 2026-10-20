// The barometer driver. GPL-3.0.
#include "pcs14/h743/bmp388.hpp"

#include <cmath>

namespace pcs14::bmp388 {

namespace {
uint16_t u16(const uint8_t* b) { return static_cast<uint16_t>(b[0] | (b[1] << 8)); }
int16_t i16(const uint8_t* b) { return static_cast<int16_t>(u16(b)); }
int8_t i8(const uint8_t* b) { return static_cast<int8_t>(b[0]); }
uint32_t u24(const uint8_t* b) { return b[0] | (b[1] << 8) | (static_cast<uint32_t>(b[2]) << 16); }
}  // namespace

Trim parse_trim(const uint8_t* b) {
  Trim t;
  t.t1 = u16(b + 0);
  t.t2 = u16(b + 2);
  t.t3 = i8(b + 4);
  t.p1 = i16(b + 5);
  t.p2 = i16(b + 7);
  t.p3 = i8(b + 9);
  t.p4 = i8(b + 10);
  t.p5 = u16(b + 11);
  t.p6 = u16(b + 13);
  t.p7 = i8(b + 15);
  t.p8 = i8(b + 16);
  t.p9 = i16(b + 17);
  t.p10 = i8(b + 19);
  t.p11 = i8(b + 20);
  return t;
}

Coefficients coefficients(const Trim& t) {
  // the datasheet's scaling, each NVM value over a power of two
  Coefficients c;
  c.t1 = t.t1 * std::ldexp(1.0, 8);
  c.t2 = t.t2 * std::ldexp(1.0, -30);
  c.t3 = t.t3 * std::ldexp(1.0, -48);
  c.p1 = (t.p1 - 16384) * std::ldexp(1.0, -20);
  c.p2 = (t.p2 - 16384) * std::ldexp(1.0, -29);
  c.p3 = t.p3 * std::ldexp(1.0, -32);
  c.p4 = t.p4 * std::ldexp(1.0, -37);
  c.p5 = t.p5 * std::ldexp(1.0, 3);
  c.p6 = t.p6 * std::ldexp(1.0, -6);
  c.p7 = t.p7 * std::ldexp(1.0, -8);
  c.p8 = t.p8 * std::ldexp(1.0, -15);
  c.p9 = t.p9 * std::ldexp(1.0, -48);
  c.p10 = t.p10 * std::ldexp(1.0, -48);
  c.p11 = t.p11 * std::ldexp(1.0, -65);
  return c;
}

uint8_t trim_crc(const uint8_t* bytes, size_t size) {
  uint8_t crc = 0xFF;
  for (size_t k = 0; k < size; ++k) {
    crc ^= bytes[k];
    for (int bit = 0; bit < 8; ++bit)
      crc = (crc & 0x80) ? static_cast<uint8_t>((crc << 1) ^ 0x1D) : static_cast<uint8_t>(crc << 1);
  }
  return static_cast<uint8_t>(crc ^ 0xFF);
}

Reading compensate(const Coefficients& c, uint32_t raw_t, uint32_t raw_p) {
  const double d = raw_t - c.t1;
  const double t = d * c.t2 + d * d * c.t3;  // degrees
  const double p = raw_p;
  const double offset = c.p5 + c.p6 * t + c.p7 * t * t + c.p8 * t * t * t;
  const double sensitivity = p * (c.p1 + c.p2 * t + c.p3 * t * t + c.p4 * t * t * t);
  const double rest = p * p * (c.p9 + c.p10 * t) + p * p * p * c.p11;
  return {offset + sensitivity + rest, t};
}

bool Barometer::start(void (*wait_ms)(uint32_t)) {
  if (!device_.write(reg::CMD, kSoftReset)) return false;
  if (wait_ms != nullptr) wait_ms(10);  // the datasheet's 2 ms start-up, with room
  uint8_t id = 0;
  if (!device_.read(reg::CHIP_ID, &id, 1) || (id != kChipId && id != kChipId390)) return false;
  uint8_t trim[kTrimBytes], stored = 0;
  if (!device_.read(reg::CALIB, trim, kTrimBytes) || !device_.read(reg::TRIM_CRC, &stored, 1))
    return false;
  if (trim_crc(trim, kTrimBytes) != stored) return false;  // a corrupt trim reads as nonsense
  c_ = coefficients(parse_trim(trim));
  return device_.write(reg::OSR, kOsr) && device_.write(reg::ODR, kOdr25Hz) &&
         device_.write(reg::CONFIG, kIirOff) && device_.write(reg::PWR_CTRL, kPwrNormal);
}

bool Barometer::read(Reading& out) {
  uint8_t bytes[7];  // STATUS, then pressure and temperature
  if (!device_.read(reg::STATUS, bytes, sizeof(bytes))) {
    ++errors_;
    return false;
  }
  if ((bytes[0] & (kPressureReady | kTemperatureReady)) != (kPressureReady | kTemperatureReady))
    return false;
  out = compensate(c_, u24(bytes + 4), u24(bytes + 1));
  return true;
}

}  // namespace pcs14::bmp388
