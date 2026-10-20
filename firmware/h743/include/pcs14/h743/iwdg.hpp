// The hardware watchdog, IWDG1: a hung loop resets the processor. GPL-3.0.
//
// The safety rules say a hung CPU means the motors stop, not the motors stuck at the last
// throttle. Two things make that true: fresh DShot frames every loop (dshot.hpp), and this.
// The independent watchdog counts down on its own 32 kHz oscillator (the LSI), so it keeps
// counting when everything else has stopped; the loop reloads it every pass, and if a pass
// doesn't come within the timeout, it resets the chip. While the flight controller reboots, its
// heartbeat stops and the safety monitor takes the ESC lines over within its 0.25 s.
//
// Once started it can't be stopped, short of a reset (RM0433, "Independent watchdog"). The
// timeout is (4 << prescaler) * (reload + 1) / LSI.
#pragma once

#include <cstdint>
#include <functional>

namespace pcs14::iwdg {

constexpr uint32_t kBase = 0x58004800;  // IWDG1, in the D3 domain (RM0433's memory map)
constexpr uint32_t KR = 0x00, PR = 0x04, RLR = 0x08, SR = 0x0C;  // register offsets
constexpr uint32_t kStart = 0xCCCC, kUnlock = 0x5555, kReload = 0xAAAA;  // KR's keys
constexpr uint32_t kLsiHz = 32000;      // typical; it varies from chip to chip
constexpr uint32_t kMaxReload = 0xFFF;  // 12 bits
// 20 ms: twenty missed passes of the 1 kHz loop, and plenty of room for a slow LSI
constexpr float kTimeoutS = 0.020f;

struct Setting {
  uint32_t prescaler;  // PR: 0 divides by 4, each step doubles it, up to 6 (256)
  uint32_t reload;     // RLR
};

// the finest setting whose timeout reaches `timeout_s` at `lsi_hz`
Setting setting_for(float timeout_s, uint32_t lsi_hz = kLsiHz);
// what a setting's timeout is at `lsi_hz`
float timeout_of(const Setting& s, uint32_t lsi_hz = kLsiHz);

// the registers, behind functions so the host tests can watch the writes
using Write = std::function<void(uint32_t offset, uint32_t value)>;
using Read = std::function<uint32_t(uint32_t offset)>;

// RM0433's order: start it, unlock the registers, set the prescaler and reload, wait for the
// update to land, then reload the counter
void start(const Setting& s, const Write& write, const Read& read);
inline void refresh(const Write& write) { write(KR, kReload); }

}  // namespace pcs14::iwdg
