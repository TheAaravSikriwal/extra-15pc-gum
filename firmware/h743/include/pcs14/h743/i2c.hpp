// A register-mapped chip on an I2C bus, as the drivers see it. GPL-3.0.
//
// The board's I2C peripheral fills these in; the host tests put a fake chip behind them.
#pragma once

#include <cstddef>
#include <cstdint>
#include <functional>

namespace pcs14::i2c {

struct Device {
  // reads `size` registers from `reg` up (the chip counts the address up); false on a NACK
  std::function<bool(uint8_t reg, uint8_t* out, size_t size)> read;
  // writes one register; false on a NACK
  std::function<bool(uint8_t reg, uint8_t value)> write;
};

}  // namespace pcs14::i2c
