// DShot out of a timer: each frame becomes a buffer of compare values that DMA feeds to the
// timer, one per bit, so the CPU only starts the transfer. GPL-3.0.
//
// A DShot bit is a fixed period with the line high for 3/4 of it for a 1 and 3/8 for a 0
// (DShot600: 1.67 us a bit, 26.7 us a frame). After the 16 bits the buffer ends in zeros, so
// the line rests low between frames. Every loop sends a fresh frame: if the processor hangs, the
// frames stop, and the ESC stops the motor (the safety rules' "a hung CPU means the motors
// stop", with the hardware watchdog behind it).
#pragma once

#include <array>
#include <cstdint>

namespace pcs14::dshot {

constexpr int kBits = 16, kRest = 2;  // the frame's bits, then two low periods
using Buffer = std::array<uint32_t, kBits + kRest>;

struct Timing {
  uint32_t period;  // timer counts a bit (the auto-reload value plus one)
  uint32_t one, zero;  // counts high for a 1 and a 0
};

// the timer's counts for DShot at `rate` bits a second (600000 for DShot600) from a timer
// clocked at `timer_hz`
Timing timing(uint32_t timer_hz, uint32_t rate);

// the compare values for one 16-bit frame (from pcs14::dshot_frame), most significant bit first
Buffer encode(uint16_t frame, const Timing& t);

// the throttle command for a share from 0 (idle, value 48) to 1 (2047); 0 is "stop", sent when
// disarmed or cut
uint16_t throttle_value(float share);

}  // namespace pcs14::dshot
