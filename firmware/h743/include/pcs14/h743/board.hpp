// The ARK FPV's wiring, as the flight firmware needs it: which of the STM32H743's pins and
// peripherals do what. GPL-3.0.
//
// From PX4's board files for the same board (boards/ark/fpv in PX4-Autopilot, BSD-3-Clause:
// timer_config.cpp, spi.cpp, board_config.h and init/rc.board_sensors), and ARK's hardware
// page, which design/catalog/components/ark-fpv.yaml quotes.
#pragma once

#include <cstdint>

namespace pcs14::board {

struct Pin {
  char port;  // 'A' to 'K'
  uint8_t pin;
};

// the motors: FMU_CH1 to CH4 on the ESC plug, timer 5's channels 4 down to 1, fed by DMA
struct MotorOutput {
  Pin pin;
  uint8_t timer, channel;
};
constexpr MotorOutput kMotors[4] = {
    {{'I', 0}, 5, 4},
    {{'H', 12}, 5, 3},
    {{'H', 11}, 5, 2},
    {{'H', 10}, 5, 1},
};
// FMU_CH5 to CH9 (the PWM_EXTRA plug): timer 8's channels 1 to 4, then timer 4's channel 1. The
// release servo and the chute's go here.
constexpr MotorOutput kExtra[5] = {
    {{'I', 5}, 8, 1}, {{'I', 6}, 8, 2}, {{'I', 7}, 8, 3}, {{'I', 2}, 8, 4}, {{'D', 12}, 4, 1},
};

// the IMU: an IIM-42653 on SPI1, chip select PI9, data ready PF2, its bus powered from PI11
constexpr uint8_t kImuSpi = 1;
constexpr Pin kImuChipSelect{'I', 9}, kImuDataReady{'F', 2}, kImuPower{'I', 11};
// as PX4 starts it: rotation 14, roll 180 then yaw 270 (pcs14/h743/iim42653.hpp applies it)
constexpr uint8_t kImuRotation = 14;

// the magnetometer: an IIS2MDC on I2C4; the barometer: a BMP388 on I2C2
constexpr uint8_t kMagI2c = 4, kBaroI2c = 2;

// the serial ports, by PX4's names
constexpr uint8_t kGpsUsart = 1;      // GPS1 (the lidar shares this plug in my wiring)
constexpr uint8_t kRcUsart = 6;       // the ExpressLRS receiver, CRSF at 420000 baud
constexpr uint8_t kTelem1Uart = 7;    // the module bus to V's companion computer
constexpr uint8_t kTelem2Uart = 5;    // the safety monitor's link
constexpr uint8_t kEscTelemUart = 4;  // the ESC's telemetry, receive only
constexpr uint8_t kConsoleUsart = 3;  // the debug console
constexpr uint32_t kCrsfBaud = 420000;

// the status LEDs, open drain, active low
constexpr Pin kLedRed{'E', 3}, kLedGreen{'E', 4}, kLedBlue{'E', 5};

// the battery's voltage through a 21:1 divider (BAT1_V_DIV 21)
constexpr float kBatteryDivider = 21.0f;

}  // namespace pcs14::board
