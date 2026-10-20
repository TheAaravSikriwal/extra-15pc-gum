// The ARK FPV's clock tree: PX4's board file's frequencies, and the reference manual's limits.
#include <doctest/doctest.h>

#include "pcs14/h743/clock.hpp"
#include "pcs14/h743/dshot.hpp"

using namespace pcs14;
using namespace pcs14::clock;

TEST_CASE("the tree gives PX4's board file's frequencies") {
  constexpr Tree t = kArkFpv;
  CHECK(vco(t) == 640000000u);
  CHECK(sysclk(t) == 320000000u);
  CHECK(pll1q(t) == 160000000u);
  CHECK(hclk(t) == 160000000u);
  CHECK(pclk1(t) == 80000000u);
  CHECK(pclk2(t) == 80000000u);
  CHECK(timer_apb1(t) == 160000000u);  // timer 5, the motors' DShot
}

TEST_CASE("inside the reference manual's limits") {
  constexpr Tree t = kArkFpv;
  CHECK(pll_range(pll_in(t)) == 3);  // 16 MHz in: the 8-16 MHz range
  CHECK(vco_ok(t));
  CHECK(flash_wait_states(hclk(t)) == 2);  // as PX4's BOARD_FLASH_WAITSTATES
  CHECK(sysclk(t) <= 480000000u);
  CHECK(hclk(t) <= 240000000u);
  CHECK(pclk1(t) <= 120000000u);
}

TEST_CASE("DShot600's bits come out right from timer 5's clock") {
  // 600 kbit/s from 160 MHz: 266.7 ticks a bit. The image used to assume 240 MHz, which on this
  // tree would have sent DShot400
  const dshot::Timing ok = dshot::timing(timer_apb1(kArkFpv), 600000);
  const dshot::Timing wrong = dshot::timing(240000000, 600000);
  const double hz = timer_apb1(kArkFpv);
  CHECK(hz / ok.period == doctest::Approx(600000).epsilon(0.01));
  CHECK(hz / wrong.period == doctest::Approx(400000).epsilon(0.01));
}
