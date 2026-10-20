// The ARK FPV's compass, an ST IIS2MDC on I2C4. GPL-3.0.
//
// The registers and the start-up follow PX4's driver for the same chip
// (src/drivers/magnetometer/st/iis2mdc, BSD-3-Clause), which is what flies on this board:
// continuous mode at 100 Hz with temperature compensation, offset cancellation, and block data
// update so a sample's bytes never mix two readings. PX4 starts it with no rotation on the ARK
// FPV (-R 0), and like PX4's, this one flips z: the chip's own axes are left-handed.
//
// The scale is the datasheet's 1.5 milligauss a count. PX4's driver uses 100/65535 (about 1.53),
// 2% more; the compass calibration on the drone takes up either.
#pragma once

#include <cstddef>
#include <cstdint>
#include <utility>

#include "pcs14/h743/i2c.hpp"
#include "pcs14/math.hpp"

namespace pcs14::iis2mdc {

constexpr uint8_t kAddress = 0x1E;  // 7-bit
namespace reg {
constexpr uint8_t WHO_AM_I = 0x4F, CFG_REG_A = 0x60, CFG_REG_B = 0x61, CFG_REG_C = 0x62;
constexpr uint8_t STATUS = 0x67, OUTX_L = 0x68;  // then x, y, z and the temperature, low byte first
}  // namespace reg
constexpr uint8_t kWhoAmI = 0x40;
// CFG_REG_A: temperature compensation, 100 Hz, continuous; B: offset cancellation; C: BDU
constexpr uint8_t kCfgA = 0x80 | 0x0C | 0x00, kCfgB = 0x02, kCfgC = 0x10;
constexpr uint8_t kNewXyz = 0x08;  // STATUS's ZYXDA: a new sample on all three axes
constexpr float kGaussPerCount = 0.0015f;
constexpr size_t kSampleBytes = 8;

struct Sample {
  Vec3 field;  // gauss, in the board's forward-right-down frame
  float temperature_c;
};

// one sample's eight bytes from OUTX_L on
Sample parse(const uint8_t* bytes);

class Compass {
 public:
  explicit Compass(i2c::Device device) : device_(std::move(device)) {}
  // checks WHO_AM_I and sets it running; false if it isn't there or won't answer
  bool start();
  // true with `out` filled when a new sample is waiting
  bool read(Sample& out);
  uint32_t errors() const { return errors_; }

 private:
  i2c::Device device_;
  uint32_t errors_ = 0;
};

}  // namespace pcs14::iis2mdc
