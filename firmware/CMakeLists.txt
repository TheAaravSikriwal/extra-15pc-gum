# My flight firmware and the safety monitor's (step 5). GPL-3.0, like the rest of the repo.
# The core builds and tests on any machine; the sim layer needs Gazebo Harmonic (inside WSL2).
#   cmake -S firmware -B build/firmware && cmake --build build/firmware && ctest --test-dir build/firmware
cmake_minimum_required(VERSION 3.22)
project(pcs14_firmware LANGUAGES CXX)

set(CMAKE_CXX_STANDARD 17)
set(CMAKE_CXX_STANDARD_REQUIRED ON)
set(CMAKE_CXX_EXTENSIONS OFF)

option(PCS14_SANITIZE "build the host tests with the address and undefined behavior sanitizers" ON)
option(PCS14_SITL "build the sim layer (needs Gazebo Harmonic)" OFF)

if(NOT MSVC)
  add_compile_options(-Wall -Wextra -Wpedantic -Wshadow -Wconversion -Wno-sign-conversion)
endif()
if(PCS14_SANITIZE AND NOT MSVC)
  add_compile_options(-fsanitize=address,undefined -fno-omit-frame-pointer)
  add_link_options(-fsanitize=address,undefined)
endif()

enable_testing()
# Python, for the checks against the flight sim's Python (pass -DPython3_EXECUTABLE to pick one)
find_package(Python3 COMPONENTS Interpreter)
add_subdirectory(core)
add_subdirectory(monitor)
if(PCS14_SITL)
  add_subdirectory(sitl)
endif()
