// The ARK FPV's clock tree, as numbers. GPL-3.0.
//
// PX4's board file for the ARK FPV (boards/ark/fpv/nuttx-config/include/board.h) is the tree
// that flies on this board, so mine is the same: the 16 MHz crystal, PLL1 at 640 MHz, the core
// at 320 MHz, the buses at 160 and 80, and every timer at twice its bus, 160 MHz. (Its comment
// says 480 MHz; its numbers say 320.) One difference: PX4 sets PLL1's input range to 4-8 MHz
// while giving it 16 MHz, and the reference manual (RM0433) puts 16 MHz in the 8-16 MHz range,
// so that's what mine sets.
//
// Everything that needs a frequency (DShot's bit timing, the UARTs' baud rates, the SPI clock)
// takes it from here, so one change to the tree moves them all. The register writes that set
// the tree up live in the board's startup; this part is plain arithmetic, tested on the host.
#pragma once

#include <cstdint>

namespace pcs14::clock {

struct Tree {
  uint32_t hse_hz = 16000000;  // the crystal
  // PLL1: in = hse / m, the oscillator at in * n, its three outputs at vco / p, q and r
  uint32_t m = 1, n = 40, p = 2, q = 4, r = 8;
  uint32_t d1cpre = 1;  // the core: sysclk / d1cpre
  uint32_t hpre = 2;    // the AHB buses: core / hpre
  uint32_t ppre1 = 2, ppre2 = 2, ppre3 = 2, ppre4 = 2;  // the APB buses: AHB / ppre
};

constexpr Tree kArkFpv{};

constexpr uint32_t pll_in(const Tree& t) { return t.hse_hz / t.m; }
constexpr uint32_t vco(const Tree& t) { return pll_in(t) * t.n; }
constexpr uint32_t sysclk(const Tree& t) { return vco(t) / t.p; }  // PLL1P
constexpr uint32_t pll1q(const Tree& t) { return vco(t) / t.q; }   // SPI1's and SDMMC's kernel
constexpr uint32_t core(const Tree& t) { return sysclk(t) / t.d1cpre; }
constexpr uint32_t hclk(const Tree& t) { return core(t) / t.hpre; }
constexpr uint32_t pclk1(const Tree& t) { return hclk(t) / t.ppre1; }
constexpr uint32_t pclk2(const Tree& t) { return hclk(t) / t.ppre2; }
// a timer runs at its bus's clock, or twice it when the bus is divided (RM0433, TIMPRE 0)
constexpr uint32_t timer_apb1(const Tree& t) { return t.ppre1 == 1 ? pclk1(t) : 2 * pclk1(t); }
constexpr uint32_t timer_apb2(const Tree& t) { return t.ppre2 == 1 ? pclk2(t) : 2 * pclk2(t); }

// PLL1RGE for its input: 0 is 1-2 MHz, 1 is 2-4, 2 is 4-8, 3 is 8-16 (RM0433); -1 if outside
constexpr int pll_range(uint32_t in_hz) {
  return in_hz < 1000000    ? -1
         : in_hz <= 2000000 ? 0
         : in_hz <= 4000000 ? 1
         : in_hz <= 8000000 ? 2
         : in_hz <= 16000000 ? 3
                             : -1;
}

// the oscillator's wide range (VCOSEL 0) runs 192 to 836 MHz (RM0433)
constexpr bool vco_ok(const Tree& t) { return vco(t) >= 192000000 && vco(t) <= 836000000; }

// flash wait states for the AXI clock (the AHB clock) at VOS1, from the table PX4's board file
// quotes: 0 up to 70 MHz, 1 to 140, 2 to 210; -1 past what VOS1 allows
constexpr int flash_wait_states(uint32_t aclk_hz) {
  return aclk_hz <= 70000000    ? 0
         : aclk_hz <= 140000000 ? 1
         : aclk_hz <= 210000000 ? 2
         : aclk_hz <= 225000000 ? 3
                                : -1;
}

}  // namespace pcs14::clock
