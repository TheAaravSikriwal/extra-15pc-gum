# The Extra 15pc Gum drag plugin for Gazebo Harmonic (gz-sim 8). Built inside WSL2 by
# scripts/setup-ubuntu.sh; Gazebo finds libpcs14-drag.so through GZ_SIM_SYSTEM_PLUGIN_PATH.
# GPL-3.0, like the rest of the repo; it links Gazebo's Apache-2.0 libraries.
cmake_minimum_required(VERSION 3.22)
project(pcs14_drag LANGUAGES CXX)

find_package(gz-plugin2 REQUIRED COMPONENTS register)
find_package(gz-sim8 REQUIRED)
find_package(gz-transport13 REQUIRED)
find_package(gz-msgs10 REQUIRED)

add_library(pcs14-drag SHARED Drag.cc)
set_target_properties(pcs14-drag PROPERTIES CXX_STANDARD 17 CXX_STANDARD_REQUIRED ON)
target_link_libraries(pcs14-drag PRIVATE
  gz-plugin2::register
  gz-sim8::gz-sim8
  gz-transport13::gz-transport13
  gz-msgs10::gz-msgs10)
