// The IIM-42653. GPL-3.0.
#include "pcs14/h743/iim42653.hpp"

namespace pcs14::iim42653 {

// PX4's settings where mine match them; the ranges, rates and FIFO packet are mine
const Write kSetup[] = {
    {reg::INT_CONFIG, 0x06},     // INT1 latched, push-pull, active low, as PX4 sets it
    {reg::FIFO_CONFIG, 0xC0},    // FIFO stop-on-full
    {reg::PWR_MGMT0, 0x0F},      // gyro and accelerometer in low-noise mode
    {reg::GYRO_CONFIG0, 0x26},   // +-2000 dps (001 in 7:5), 1 kHz (0110)
    {reg::ACCEL_CONFIG0, 0x26},  // +-16 g (001 in 7:5), 1 kHz (0110)
    {reg::FIFO_CONFIG1, 0x07},   // accelerometer, gyro and temperature into the FIFO, 16-bit
};
const size_t kSetupCount = sizeof(kSetup) / sizeof(kSetup[0]);

namespace {
int16_t be16(const uint8_t* p) { return static_cast<int16_t>((p[0] << 8) | p[1]); }

// the chip's frame to the board's: roll 180, then yaw 270 (PX4's rotation 14 on this board)
Vec3 to_board(const Vec3& v) {
  static const Quat r = Quat::from_euler(kPi, 0, 1.5f * kPi);
  return r.rotate(v);
}
}  // namespace

uint8_t Imu::read_register(uint8_t address) {
  const uint8_t tx[2] = {static_cast<uint8_t>(address | reg::READ), 0};
  uint8_t rx[2] = {};
  transfer_(tx, rx, 2);
  return rx[1];
}

void Imu::write_register(uint8_t address, uint8_t value) {
  const uint8_t tx[2] = {address, value};
  uint8_t rx[2] = {};
  transfer_(tx, rx, 2);
}

bool Imu::start() {
  write_register(reg::REG_BANK_SEL, 0);
  write_register(reg::DEVICE_CONFIG, 0x01);  // soft reset
  delay_(2000);                              // the datasheet asks for 1 ms; PX4 waits 2
  if (read_register(reg::WHO_AM_I) != kWhoAmI) return false;
  for (size_t k = 0; k < kSetupCount; ++k) write_register(kSetup[k].address, kSetup[k].value);
  delay_(1000);
  write_register(reg::SIGNAL_PATH_RESET, 0x02);  // flush the FIFO: start clean
  return true;
}

size_t Imu::read(Sample* out, size_t max) {
  // the count, then that many bytes in one burst
  const uint8_t ask[3] = {static_cast<uint8_t>(reg::FIFO_COUNTH | reg::READ), 0, 0};
  uint8_t count[3] = {};
  transfer_(ask, count, 3);
  size_t bytes = static_cast<size_t>((count[1] << 8) | count[2]);
  size_t packets = bytes / kPacket;
  if (packets > max) packets = max;
  if (packets == 0) return 0;
  uint8_t tx[1 + kPacket * 32] = {static_cast<uint8_t>(reg::FIFO_DATA | reg::READ)};
  uint8_t rx[1 + kPacket * 32] = {};
  if (packets > 32) packets = 32;
  transfer_(tx, rx, 1 + packets * kPacket);
  size_t got = 0;
  for (size_t k = 0; k < packets; ++k) {
    if (parse(rx + 1 + k * kPacket, out[got])) ++got;
    else ++bad_;
  }
  return got;
}

bool parse(const uint8_t* p, Sample& out) {
  const uint8_t header = p[0];
  // bit 7 set: the FIFO was empty; bits 6 and 5: accelerometer and gyro present; bit 4: the
  // 20-bit packet, which this doesn't ask for
  if ((header & 0x80) || (header & 0x60) != 0x60 || (header & 0x10)) return false;
  const Vec3 accel{static_cast<float>(be16(p + 1)), static_cast<float>(be16(p + 3)),
                   static_cast<float>(be16(p + 5))};
  const Vec3 gyro{static_cast<float>(be16(p + 7)), static_cast<float>(be16(p + 9)),
                  static_cast<float>(be16(p + 11))};
  out.accel = to_board(accel * kAccelPerLsb);
  out.gyro = to_board(gyro * kGyroPerLsb);
  out.temperature_c = static_cast<float>(static_cast<int8_t>(p[13])) / 2.07f + 25.0f;
  out.timestamp = static_cast<uint16_t>((p[14] << 8) | p[15]);
  return true;
}

}  // namespace pcs14::iim42653
