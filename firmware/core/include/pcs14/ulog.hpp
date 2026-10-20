// Writing PX4's log format, ULog, so the flight sim's graders read my firmware's flights the
// same way they read PX4's. GPL-3.0.
//
// A ULog file is a 16-byte header, then messages, each a 3-byte header (size, type) and its
// body: formats ('F', a topic's fields as text), info ('I'), parameters ('P'), subscriptions
// ('A', a topic and its id), data ('D', one sample) and logged text ('L'). The layout follows
// PX4's documentation of the format (docs.px4.io, "ULog File Format").
//
// The writer doesn't touch files: it hands bytes to a sink, so the same code writes to a file
// in the sim, to the SD card on the drone and to a buffer in the tests.
#pragma once

#include <cstddef>
#include <cstdint>
#include <cstring>
#include <functional>
#include <string>

namespace pcs14 {

class ULogWriter {
 public:
  using Sink = std::function<void(const uint8_t* data, size_t size)>;

  explicit ULogWriter(Sink sink) : sink_(std::move(sink)) {}

  // the file header and the flag bits; first, once
  void begin(uint64_t start_us);
  // a topic's fields, as "name:type field;type field;..." (types as PX4 writes them: uint64_t,
  // float, bool, int32_t, a nested topic's name, and arrays as float[3])
  void format(const std::string& text);
  // a piece of text information about the log, such as sys_name
  void info(const std::string& name, const std::string& value);
  void parameter(const std::string& name, float value);
  void parameter(const std::string& name, int32_t value);
  // a topic the log will carry; returns its id for data()
  uint16_t subscribe(const std::string& topic, uint8_t instance = 0);
  // one sample: the topic's fields packed in its format's order, no padding
  void data(uint16_t id, const uint8_t* fields, size_t size);
  // a line of text, as PX4 logs its messages; level as syslog's (6 info, 4 warning, 3 error)
  void text(uint8_t level, uint64_t t_us, const std::string& message);

 private:
  void message(char type, const uint8_t* body, size_t size);
  Sink sink_;
  uint16_t next_id_ = 0;
};

// packs a sample's fields, in order, the way ULog lays them out (little-endian, no padding)
class Packer {
 public:
  template <typename T>
  Packer& put(T value) {
    static_assert(sizeof(T) <= 8, "one field at a time");
    uint8_t raw[sizeof(T)];
    std::memcpy(raw, &value, sizeof(T));
    for (size_t k = 0; k < sizeof(T); ++k) bytes_[size_++] = raw[k];
    return *this;
  }
  Packer& put_bool(bool value) { return put(static_cast<uint8_t>(value ? 1 : 0)); }
  const uint8_t* data() const { return bytes_; }
  size_t size() const { return size_; }

 private:
  uint8_t bytes_[256]{};
  size_t size_ = 0;
};

}  // namespace pcs14
