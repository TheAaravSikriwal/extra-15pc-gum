// The compass driver. GPL-3.0.
#include "pcs14/h743/iis2mdc.hpp"

namespace pcs14::iis2mdc {

namespace {
int16_t word(const uint8_t* b) { return static_cast<int16_t>(b[0] | (b[1] << 8)); }
}  // namespace

Sample parse(const uint8_t* b) {
  Sample s;
  s.field = Vec3{static_cast<float>(word(b)), static_cast<float>(word(b + 2)),
                 -static_cast<float>(word(b + 4))} *
            kGaussPerCount;
  s.temperature_c = static_cast<float>(word(b + 6)) / 8 + 25;  // 8 counts a degree, 0 at 25
  return s;
}

bool Compass::start() {
  uint8_t id = 0;
  if (!device_.read(reg::WHO_AM_I, &id, 1) || id != kWhoAmI) return false;
  return device_.write(reg::CFG_REG_A, kCfgA) && device_.write(reg::CFG_REG_B, kCfgB) &&
         device_.write(reg::CFG_REG_C, kCfgC);
}

bool Compass::read(Sample& out) {
  uint8_t status = 0;
  if (!device_.read(reg::STATUS, &status, 1)) {
    ++errors_;
    return false;
  }
  if ((status & kNewXyz) == 0) return false;
  uint8_t bytes[kSampleBytes];
  if (!device_.read(reg::OUTX_L, bytes, kSampleBytes)) {
    ++errors_;
    return false;
  }
  out = parse(bytes);
  return true;
}

}  // namespace pcs14::iis2mdc
