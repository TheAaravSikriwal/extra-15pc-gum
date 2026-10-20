// DShot out of a timer. GPL-3.0.
#include "pcs14/h743/dshot.hpp"

namespace pcs14::dshot {

Timing timing(uint32_t timer_hz, uint32_t rate) {
  const uint32_t period = (timer_hz + rate / 2) / rate;
  return {period, (period * 3 + 2) / 4, (period * 3 + 4) / 8};
}

Buffer encode(uint16_t frame, const Timing& t) {
  Buffer b{};
  for (int k = 0; k < kBits; ++k) b[k] = (frame & (0x8000u >> k)) ? t.one : t.zero;
  return b;  // the rest stay 0: the line low
}

uint16_t throttle_value(float share) {
  if (!(share > 0)) return 48;
  if (share >= 1) return 2047;
  return static_cast<uint16_t>(48 + share * (2047 - 48) + 0.5f);
}

}  // namespace pcs14::dshot
