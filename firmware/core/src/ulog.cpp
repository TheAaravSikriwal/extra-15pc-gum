// Writing ULog. GPL-3.0.
#include "pcs14/ulog.hpp"

#include <vector>

namespace pcs14 {

namespace {
template <typename T>
void append(std::vector<uint8_t>& out, T value) {
  uint8_t raw[sizeof(T)];
  std::memcpy(raw, &value, sizeof(T));
  out.insert(out.end(), raw, raw + sizeof(T));
}
void append(std::vector<uint8_t>& out, const std::string& text) {
  out.insert(out.end(), text.begin(), text.end());
}
}  // namespace

void ULogWriter::begin(uint64_t start_us) {
  // "ULog", 0x01 0x12 0x35, then the version and when the log started
  std::vector<uint8_t> header = {'U', 'L', 'o', 'g', 0x01, 0x12, 0x35, 0x01};
  append(header, start_us);
  sink_(header.data(), header.size());
  // the flag bits: nothing incompatible, nothing appended
  std::vector<uint8_t> flags(8 + 8 + 3 * 8, 0);
  message('B', flags.data(), flags.size());
}

void ULogWriter::message(char type, const uint8_t* body, size_t size) {
  std::vector<uint8_t> out;
  append(out, static_cast<uint16_t>(size));
  out.push_back(static_cast<uint8_t>(type));
  out.insert(out.end(), body, body + size);
  sink_(out.data(), out.size());
}

void ULogWriter::format(const std::string& text) {
  message('F', reinterpret_cast<const uint8_t*>(text.data()), text.size());
}

void ULogWriter::info(const std::string& name, const std::string& value) {
  std::vector<uint8_t> body;
  const std::string key = "char[" + std::to_string(value.size()) + "] " + name;
  body.push_back(static_cast<uint8_t>(key.size()));
  append(body, key);
  append(body, value);
  message('I', body.data(), body.size());
}

void ULogWriter::parameter(const std::string& name, float value) {
  std::vector<uint8_t> body;
  const std::string key = "float " + name;
  body.push_back(static_cast<uint8_t>(key.size()));
  append(body, key);
  append(body, value);
  message('P', body.data(), body.size());
}

void ULogWriter::parameter(const std::string& name, int32_t value) {
  std::vector<uint8_t> body;
  const std::string key = "int32_t " + name;
  body.push_back(static_cast<uint8_t>(key.size()));
  append(body, key);
  append(body, value);
  message('P', body.data(), body.size());
}

uint16_t ULogWriter::subscribe(const std::string& topic, uint8_t instance) {
  const uint16_t id = next_id_++;
  std::vector<uint8_t> body;
  body.push_back(instance);
  append(body, id);
  append(body, topic);
  message('A', body.data(), body.size());
  return id;
}

void ULogWriter::data(uint16_t id, const uint8_t* fields, size_t size) {
  std::vector<uint8_t> body;
  append(body, id);
  body.insert(body.end(), fields, fields + size);
  message('D', body.data(), body.size());
}

void ULogWriter::text(uint8_t level, uint64_t t_us, const std::string& message_text) {
  std::vector<uint8_t> body;
  body.push_back(static_cast<uint8_t>('0' + level));
  append(body, t_us);
  append(body, message_text);
  message('L', body.data(), body.size());
}

}  // namespace pcs14
