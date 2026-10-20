# The sim layer: the core as a Linux program flying a Gazebo model, in place of PX4.
# Needs Gazebo Harmonic's transport and messages (Ubuntu's libgz-transport13-dev and
# libgz-msgs10-dev, which the flight sim's setup installs with Gazebo).
find_package(gz-transport13 REQUIRED)
find_package(gz-msgs10 REQUIRED)

add_executable(pcs14_sitl src/main.cpp)
target_link_libraries(pcs14_sitl PRIVATE pcs14_core gz-transport13::gz-transport13 gz-msgs10::gz-msgs10)
# Gazebo's and protobuf's headers aren't written for this many warnings
target_compile_options(pcs14_sitl PRIVATE -Wno-conversion -Wno-shadow -Wno-pedantic)
