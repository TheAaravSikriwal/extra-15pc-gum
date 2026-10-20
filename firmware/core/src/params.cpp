// Parameters. GPL-3.0.
#include "pcs14/params.hpp"

namespace pcs14 {

const Params::Param* Params::find(const std::string& name, size_t* index) const {
  for (size_t k = 0; k < list_.size(); ++k) {
    if (list_[k].name == name) {
      if (index != nullptr) *index = k;
      return &list_[k];
    }
  }
  return nullptr;
}

Params::Param* Params::find_mutable(const std::string& name, size_t* index) {
  return const_cast<Param*>(find(name, index));
}

void Params::add(const std::string& name, float value) {
  if (find(name) == nullptr) list_.push_back({name.substr(0, 16), Type::Float, value, 0});
}

void Params::add_int(const std::string& name, int32_t value) {
  if (find(name) == nullptr) list_.push_back({name.substr(0, 16), Type::Int32, 0, value});
}

float Params::get(const std::string& name, float fallback) const {
  const Param* p = find(name);
  return p == nullptr ? fallback : p->value();
}

int32_t Params::get_int(const std::string& name, int32_t fallback) const {
  const Param* p = find(name);
  if (p == nullptr) return fallback;
  return p->type == Type::Int32 ? p->i : static_cast<int32_t>(p->f);
}

size_t Params::set(const std::string& name, float value) {
  size_t index = 0;
  if (Param* p = find_mutable(name, &index)) {
    if (p->type == Type::Float) p->f = value;
    else p->i = static_cast<int32_t>(value);
    return index;
  }
  list_.push_back({name.substr(0, 16), Type::Float, value, 0});
  return list_.size() - 1;
}

size_t Params::set_int(const std::string& name, int32_t value) {
  size_t index = 0;
  if (Param* p = find_mutable(name, &index)) {
    if (p->type == Type::Int32) p->i = value;
    else p->f = static_cast<float>(value);
    return index;
  }
  list_.push_back({name.substr(0, 16), Type::Int32, 0, value});
  return list_.size() - 1;
}

}  // namespace pcs14
