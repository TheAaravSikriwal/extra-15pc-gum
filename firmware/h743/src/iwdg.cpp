// The hardware watchdog. GPL-3.0.
#include "pcs14/h743/iwdg.hpp"

namespace pcs14::iwdg {

float timeout_of(const Setting& s, uint32_t lsi_hz) {
  return static_cast<float>(4u << s.prescaler) * static_cast<float>(s.reload + 1) /
         static_cast<float>(lsi_hz);
}

Setting setting_for(float timeout_s, uint32_t lsi_hz) {
  for (uint32_t pr = 0; pr <= 6; ++pr) {
    const float tick = static_cast<float>(4u << pr) / static_cast<float>(lsi_hz);
    const float counts = timeout_s / tick;
    if (counts <= static_cast<float>(kMaxReload + 1)) {
      uint32_t reload = static_cast<uint32_t>(counts + 0.5f);
      reload = reload == 0 ? 0 : reload - 1;
      return {pr, reload};
    }
  }
  return {6, kMaxReload};  // the longest it can do, about 32 s
}

void start(const Setting& s, const Write& write, const Read& read) {
  write(KR, kStart);
  write(KR, kUnlock);
  write(PR, s.prescaler);
  write(RLR, s.reload);
  // the new values cross into the watchdog's own clock domain; SR's bits clear once they have
  for (int tries = 0; tries < 100000 && (read(SR) & 0x7) != 0; ++tries) {
  }
  write(KR, kReload);
}

}  // namespace pcs14::iwdg
