// The SD card's flight log. GPL-3.0.
#include "pcs14/h743/sdlog.hpp"

#include <cstdio>

extern "C" {
#include "diskio.h"
}

namespace pcs14::sdlog {

namespace {
// FatFs talks to one drive (FF_VOLUMES 1) through the diskio functions below; this is it
BlockDevice* g_device = nullptr;
}  // namespace

}  // namespace pcs14::sdlog

using pcs14::sdlog::g_device;

extern "C" {

DSTATUS disk_status(BYTE drive) { return drive == 0 && g_device != nullptr ? 0 : STA_NOINIT; }

DSTATUS disk_initialize(BYTE drive) { return disk_status(drive); }

DRESULT disk_read(BYTE drive, BYTE* buffer, LBA_t sector, UINT count) {
  if (drive != 0 || g_device == nullptr) return RES_NOTRDY;
  return g_device->read(buffer, static_cast<uint32_t>(sector), count) ? RES_OK : RES_ERROR;
}

DRESULT disk_write(BYTE drive, const BYTE* buffer, LBA_t sector, UINT count) {
  if (drive != 0 || g_device == nullptr) return RES_NOTRDY;
  return g_device->write(buffer, static_cast<uint32_t>(sector), count) ? RES_OK : RES_ERROR;
}

DRESULT disk_ioctl(BYTE drive, BYTE command, void* buffer) {
  if (drive != 0 || g_device == nullptr) return RES_NOTRDY;
  switch (command) {
    case CTRL_SYNC:
      return RES_OK;  // the device writes through
    case GET_SECTOR_COUNT:
      *static_cast<LBA_t*>(buffer) = g_device->sectors();
      return RES_OK;
    case GET_SECTOR_SIZE:
      *static_cast<WORD*>(buffer) = pcs14::sdlog::kSectorBytes;
      return RES_OK;
    case GET_BLOCK_SIZE:
      *static_cast<DWORD*>(buffer) = 1;  // unknown erase block
      return RES_OK;
    default:
      return RES_PARERR;
  }
}

}  // extern "C"

namespace pcs14::sdlog {

Logger::Logger(BlockDevice& device) { g_device = &device; }

Logger::~Logger() {
  if (open_) f_close(&file_);
  if (mounted_) f_unmount("");
}

bool Logger::format() {
  static BYTE work[FF_MAX_SS];
  const MKFS_PARM how = {FM_ANY, 0, 0, 0, 0};
  return f_mkfs("", &how, work, sizeof(work)) == FR_OK;
}

bool Logger::mount() {
  mounted_ = f_mount(&fs_, "", 1) == FR_OK;
  return mounted_;
}

bool Logger::open_next() {
  if (!mounted_) return false;
  if (open_ && !close()) return false;
  for (int k = 1; k <= 99999; ++k) {
    std::snprintf(name_, sizeof(name_), "LOG%05d.ULG", k);
    FILINFO info;
    if (f_stat(name_, &info) == FR_NO_FILE) {
      open_ = f_open(&file_, name_, FA_WRITE | FA_CREATE_NEW) == FR_OK;
      failed_ = !open_;
      return open_;
    }
  }
  return false;  // a full card's worth of names
}

bool Logger::write(const uint8_t* data, size_t size) {
  if (!open_ || failed_) return false;
  UINT done = 0;
  if (f_write(&file_, data, static_cast<UINT>(size), &done) != FR_OK || done != size) {
    failed_ = true;
    return false;
  }
  return true;
}

bool Logger::sync() { return open_ && !failed_ && f_sync(&file_) == FR_OK; }

bool Logger::close() {
  if (!open_) return true;
  open_ = false;
  return f_close(&file_) == FR_OK && !failed_;
}

bool read_whole(const char* name, std::vector<uint8_t>& out) {
  FIL file{};
  if (f_open(&file, name, FA_READ) != FR_OK) return false;
  out.resize(static_cast<size_t>(f_size(&file)));
  UINT done = 0;
  const bool ok = f_read(&file, out.data(), static_cast<UINT>(out.size()), &done) == FR_OK &&
                  done == out.size();
  f_close(&file);
  return ok;
}

}  // namespace pcs14::sdlog
