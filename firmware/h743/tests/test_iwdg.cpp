// The hardware watchdog: its timeout arithmetic and the reference manual's start order.
#include <doctest/doctest.h>

#include <utility>
#include <vector>

#include "pcs14/h743/iwdg.hpp"

using namespace pcs14;
using namespace pcs14::iwdg;
using doctest::Approx;

TEST_CASE("20 ms at 32 kHz: the finest prescaler that reaches it") {
  const Setting s = setting_for(kTimeoutS);
  CHECK(s.prescaler == 0);  // ticks of 4 / 32 kHz, 125 us
  CHECK(s.reload == 159);   // 160 ticks
  CHECK(timeout_of(s) == Approx(0.020f));
  // a slow LSI stretches it, a fast one shortens it; the loop's 1 ms passes stay far inside
  CHECK(timeout_of(s, 29000) < 0.025f);
  CHECK(timeout_of(s, 35000) > 0.018f);
}

TEST_CASE("long timeouts move up the prescaler, and the longest is about 32 s") {
  const Setting two = setting_for(2.0f);
  CHECK(two.reload <= kMaxReload);
  CHECK(timeout_of(two) == Approx(2.0f).epsilon(0.01));
  CHECK(timeout_of(setting_for(100.0f)) == Approx(32.768f).epsilon(0.001));
}

TEST_CASE("started in the reference manual's order, and refreshed with its key") {
  std::vector<std::pair<uint32_t, uint32_t>> writes;
  int busy = 3;  // SR shows the update still crossing for a few reads
  const Write write = [&](uint32_t offset, uint32_t value) { writes.push_back({offset, value}); };
  const Read read = [&](uint32_t offset) -> uint32_t {
    return offset == SR && busy-- > 0 ? 0x3 : 0;
  };
  start({0, 159}, write, read);
  const std::vector<std::pair<uint32_t, uint32_t>> want{
      {KR, kStart}, {KR, kUnlock}, {PR, 0}, {RLR, 159}, {KR, kReload}};
  CHECK(writes == want);
  CHECK(busy < 0);  // it waited for the update
  refresh(write);
  CHECK(writes.back() == std::make_pair(KR, kReload));
}
