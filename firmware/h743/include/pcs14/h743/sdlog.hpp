// The flight log on the ARK FPV's microSD card: the ULog stream, onto a FAT card. GPL-3.0.
//
// FatFs R0.16 (ChaN, 1-clause BSD) is the file system. The card sits behind a block device,
// the SDMMC peripheral on the board and a RAM disk in the host tests, so this part is tested
// on my PC. Each flight gets the next free name, LOG00001.ULG and up, like PX4's numbered logs
// (8.3 names: long file names would pull in FatFs's 2 MB of Unicode tables for nothing). A card
// that stops taking writes is flagged rather than ignored, so the ground station can say so.
#pragma once

#include <cstddef>
#include <cstdint>
#include <vector>

extern "C" {
#include "ff.h"
}

namespace pcs14::sdlog {

constexpr uint32_t kSectorBytes = 512;

struct BlockDevice {
  virtual ~BlockDevice() = default;
  virtual bool read(uint8_t* out, uint32_t sector, uint32_t count) = 0;
  virtual bool write(const uint8_t* in, uint32_t sector, uint32_t count) = 0;
  virtual uint32_t sectors() const = 0;
};

class Logger {
 public:
  explicit Logger(BlockDevice& device);
  ~Logger();
  Logger(const Logger&) = delete;
  Logger& operator=(const Logger&) = delete;

  bool format();  // a FAT file system over the whole card; the tests' blank RAM disks need it
  bool mount();
  bool open_next();  // the next free LOGnnnnn.ULG
  bool write(const uint8_t* data, size_t size);
  bool sync();  // what's written so far, safe on the card even if the power goes
  bool close();

  const char* name() const { return name_; }
  bool failed() const { return failed_; }

 private:
  FATFS fs_{};
  FIL file_{};
  bool mounted_ = false, open_ = false, failed_ = false;
  char name_[13] = {};
};

// a whole file read back off the mounted card, for the tests and for pulling a log off it
bool read_whole(const char* name, std::vector<uint8_t>& out);

}  // namespace pcs14::sdlog
