// The ARK FPV's IMU, a TDK InvenSense IIM-42653 on SPI1, read through its FIFO. GPL-3.0.
//
// The registers and the start-up order follow PX4's driver for the same chip
// (src/drivers/imu/invensense/iim42653, BSD-3-Clause), which is what flies on this board. Mine
// is simpler: the 16-byte FIFO packets (accelerometer, gyro, temperature, timestamp) at 1 kHz,
// +-16 g and +-2000 degrees a second, rather than PX4's 20-bit packets at 8 kHz.
//
// The chip sits on the board turned roll 180, yaw 270 from the board's forward-right-down
// (PX4 starts it with -R 14 on the ARK FPV), so each sample is turned into the board's frame.
// The bus is an interface, so the host tests can put a fake chip behind it.
#pragma once

#include <cstddef>
#include <cstdint>
#include <functional>

#include "pcs14/math.hpp"

namespace pcs14::iim42653 {

namespace reg {  // bank 0, from PX4's InvenSense_IIM42653_registers.hpp
constexpr uint8_t DEVICE_CONFIG = 0x11, INT_CONFIG = 0x14, FIFO_CONFIG = 0x16;
constexpr uint8_t FIFO_COUNTH = 0x2E, FIFO_DATA = 0x30, SIGNAL_PATH_RESET = 0x4B;
constexpr uint8_t PWR_MGMT0 = 0x4E, GYRO_CONFIG0 = 0x4F, ACCEL_CONFIG0 = 0x50;
constexpr uint8_t FIFO_CONFIG1 = 0x5F, WHO_AM_I = 0x75, REG_BANK_SEL = 0x76;
constexpr uint8_t READ = 0x80;
}  // namespace reg

constexpr uint8_t kWhoAmI = 0x56;
constexpr size_t kPacket = 16;  // header, accel x y z, gyro x y z, temperature, timestamp
constexpr float kAccelPerLsb = 9.80665f / 2048;              // +-16 g
constexpr float kGyroPerLsb = 3.14159265f / 180 / 16.4f;     // +-2000 degrees a second

// the register writes, in order, after the soft reset (address, value)
struct Write {
  uint8_t address, value;
};
extern const Write kSetup[];
extern const size_t kSetupCount;

// a full-duplex SPI transfer with the chip selected: `size` bytes out of `tx`, into `rx`
using Transfer = std::function<void(const uint8_t* tx, uint8_t* rx, size_t size)>;
using Delay = std::function<void(uint32_t microseconds)>;

struct Sample {
  Vec3 accel, gyro;  // m/s^2 and rad/s, in the board's forward-right-down frame
  float temperature_c;
  uint16_t timestamp;  // the chip's own, in its ticks
};

class Imu {
 public:
  Imu(Transfer transfer, Delay delay) : transfer_(std::move(transfer)), delay_(std::move(delay)) {}

  // resets and configures it; false if it isn't there (the wrong WHO_AM_I)
  bool start();
  // reads whatever the FIFO holds, up to `max` samples; returns how many
  size_t read(Sample* out, size_t max);
  uint32_t bad_packets() const { return bad_; }

  uint8_t read_register(uint8_t address);
  void write_register(uint8_t address, uint8_t value);

 private:
  Transfer transfer_;
  Delay delay_;
  uint32_t bad_ = 0;
};

// one FIFO packet into a sample in the board's frame; false if it isn't a full accel and gyro
// packet (an empty FIFO reads as 0xFF or 0x80 headers)
bool parse(const uint8_t* packet, Sample& out);

}  // namespace pcs14::iim42653
