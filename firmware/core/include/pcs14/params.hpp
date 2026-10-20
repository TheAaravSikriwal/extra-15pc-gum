// Parameters: named settings the ground station can read and change, PX4-style. GPL-3.0.
//
// Each has a name of up to 16 characters and is a float or an int32, like PX4's. The flight
// code reads them by name; MAVLink reads and writes them (pcs14/link.hpp). Unknown names can be
// set too, so a ground station's habits (MAVSDK sets PX4's names) don't fail; the flight code
// only reads the ones it knows.
#pragma once

#include <cstdint>
#include <string>
#include <vector>

namespace pcs14 {

class Params {
 public:
  enum class Type : uint8_t { Int32, Float };
  struct Param {
    std::string name;
    Type type;
    float f = 0;
    int32_t i = 0;
    float value() const { return type == Type::Float ? f : static_cast<float>(i); }
  };

  // declares a parameter with its default; declaring it again keeps the value it has
  void add(const std::string& name, float value);
  void add_int(const std::string& name, int32_t value);

  // the value, or `fallback` if no parameter has that name
  float get(const std::string& name, float fallback = 0) const;
  int32_t get_int(const std::string& name, int32_t fallback = 0) const;

  // sets one, adding it if it's new; returns its index
  size_t set(const std::string& name, float value);
  size_t set_int(const std::string& name, int32_t value);

  const Param* find(const std::string& name, size_t* index = nullptr) const;
  const Param& at(size_t index) const { return list_[index]; }
  size_t size() const { return list_.size(); }

 private:
  Param* find_mutable(const std::string& name, size_t* index);
  std::vector<Param> list_;
};

}  // namespace pcs14
