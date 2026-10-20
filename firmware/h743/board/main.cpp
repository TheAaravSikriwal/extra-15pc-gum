// My flight firmware on the ARK FPV: the main loop. GPL-3.0.
//
// What runs here is the same core the sim flies (pcs14/flight.hpp): one IMU sample in, four
// motor speeds out, at the IMU's rate. The hardware around it comes driver by driver, each
// tested on the host first (firmware/h743/tests):
//   done: the IMU's registers and FIFO (iim42653), CRSF from the receiver, DShot buffers
//   next: the clock tree, SPI1 and its DMA, timer 5's DMA for DShot, USART6, the watchdog,
//         the magnetometer and barometer on I2C, DroneCAN for the GPS, the SD card's log
// Until those are in, the hardware hooks below are stubs, and the image only proves that the
// flight code builds and links for the board.
#include <cstdint>

#include "pcs14/flight.hpp"
#include "pcs14/h743/board.hpp"
#include "pcs14/h743/crsf.hpp"  // the receiver, next to come in (crsf::Parser)
#include "pcs14/h743/dshot.hpp"
#include "pcs14/h743/iim42653.hpp"
#include "pcs14/monitor.hpp"

namespace {

// the hardware hooks, stubbed until their drivers come
void spi1_transfer(const uint8_t*, uint8_t* rx, size_t n) {
  for (size_t k = 0; k < n; ++k) rx[k] = 0xFF;  // nothing on the bus yet
}
void delay_us(uint32_t) {}
void motors_send(const pcs14::dshot::Buffer (&)[4]) {}
void watchdog_refresh() {}

// base's numbers, until the airframe comes from parameters on the SD card
pcs14::Airframe airframe() {
  pcs14::Airframe a;
  a.mass_kg = 1.86f;
  a.inertia = {0.0129f, 0.0155f, 0.0260f};
  constexpr float x = 0.1485f;
  a.mixer.rotors = {{{x, x, 0.016f}, {-x, -x, 0.016f}, {x, -x, -0.016f}, {-x, x, -0.016f}}};
  a.mixer.motor_constant = 1.5777e-5f;
  a.mixer.idle_rad_s = 142.0f;
  a.mixer.max_rad_s = 947.0f;
  return a;
}

}  // namespace

int main() {
  const pcs14::Airframe frame = airframe();
  static pcs14::Flight flight(frame);
  static pcs14::iim42653::Imu imu(spi1_transfer, delay_us);
  const pcs14::dshot::Timing timing = pcs14::dshot::timing(240000000, 600000);
  const bool have_imu = imu.start();
  pcs14::iim42653::Sample samples[8];
  while (true) {
    watchdog_refresh();
    const size_t n = have_imu ? imu.read(samples, 8) : 0;
    pcs14::Mix mix{};
    for (size_t k = 0; k < n; ++k) mix = flight.step(samples[k].gyro, samples[k].accel, 0.001f);
    // a fresh frame for every motor, every loop: stop when disarmed. DShot's throttle is close
    // to a share of the motor's speed range, idle to top
    pcs14::dshot::Buffer frames[4];
    const float idle = frame.mixer.idle_rad_s, span = frame.mixer.max_rad_s - idle;
    for (int i = 0; i < 4; ++i) {
      const uint16_t value = flight.armed()
                                 ? pcs14::dshot::throttle_value((mix.rad_s[i] - idle) / span)
                                 : pcs14::kDshotStop;
      frames[i] = pcs14::dshot::encode(pcs14::dshot_frame(value), timing);
    }
    motors_send(frames);
  }
}
