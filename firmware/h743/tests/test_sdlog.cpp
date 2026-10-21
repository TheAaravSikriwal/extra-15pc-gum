// The SD card's flight log: FatFs on a RAM disk standing in for the card.
#include <doctest/doctest.h>

#include <cstring>
#include <string>
#include <vector>

#include "pcs14/h743/sdlog.hpp"
#include "pcs14/ulog.hpp"

using namespace pcs14;
using namespace pcs14::sdlog;

namespace {
struct RamDisk : BlockDevice {
  std::vector<uint8_t> bytes;
  bool fail_writes = false;
  explicit RamDisk(uint32_t sectors) : bytes(static_cast<size_t>(sectors) * kSectorBytes) {}
  bool read(uint8_t* out, uint32_t sector, uint32_t count) override {
    std::memcpy(out, &bytes[static_cast<size_t>(sector) * kSectorBytes], count * kSectorBytes);
    return true;
  }
  bool write(const uint8_t* in, uint32_t sector, uint32_t count) override {
    if (fail_writes) return false;
    std::memcpy(&bytes[static_cast<size_t>(sector) * kSectorBytes], in, count * kSectorBytes);
    return true;
  }
  uint32_t sectors() const override {
    return static_cast<uint32_t>(bytes.size() / kSectorBytes);
  }
};
}  // namespace

TEST_CASE("a flight's ULog goes onto the card under the next free name, and reads back whole") {
  RamDisk disk(16384);  // 8 MB
  Logger log(disk);
  REQUIRE(log.format());
  REQUIRE(log.mount());
  REQUIRE(log.open_next());
  CHECK(std::string(log.name()) == "LOG00001.ULG");
  std::vector<uint8_t> sent;
  ULogWriter out([&](const uint8_t* d, size_t n) {
    sent.insert(sent.end(), d, d + n);
    CHECK(log.write(d, n));
  });
  out.begin(0);
  out.info("sys_name", "pcs14");
  for (int k = 0; k < 2000; ++k) out.text(6, static_cast<uint64_t>(k) * 1000, "a line of log");
  REQUIRE(log.close());
  CHECK(sent.size() > 40000);  // more than one cluster, so FatFs had to chain them

  std::vector<uint8_t> back;
  REQUIRE(read_whole("LOG00001.ULG", back));
  CHECK(back == sent);

  REQUIRE(log.open_next());  // the next flight's
  CHECK(std::string(log.name()) == "LOG00002.ULG");
  REQUIRE(log.close());
}

TEST_CASE("a card that stops taking writes is noticed, not ignored") {
  RamDisk disk(16384);
  Logger log(disk);
  REQUIRE(log.format());
  REQUIRE(log.mount());
  REQUIRE(log.open_next());
  disk.fail_writes = true;
  std::vector<uint8_t> chunk(kSectorBytes * 8, 0x55);
  bool ok = true;
  for (int k = 0; k < 4 && ok; ++k) ok = log.write(chunk.data(), chunk.size());
  CHECK_FALSE(ok);
  CHECK(log.failed());
}
