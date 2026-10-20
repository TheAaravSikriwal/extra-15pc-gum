# The safety monitor (the Teensy 4.1 in Base): its core, tested on the host. Its attitude comes
# from the flight core's estimator, on its own IMU.
add_library(pcs14_monitor STATIC src/monitor.cpp)
target_include_directories(pcs14_monitor PUBLIC include)
target_link_libraries(pcs14_monitor PUBLIC pcs14_core)

if(NOT CMAKE_CROSSCOMPILING)  # the tests run on the host only
add_executable(pcs14_monitor_tests ../core/tests/main.cpp tests/test_monitor.cpp)
target_link_libraries(pcs14_monitor_tests PRIVATE pcs14_monitor doctest::doctest)
add_test(NAME monitor COMMAND pcs14_monitor_tests)

# the triggers against the Python reference, on the same samples
add_executable(pcs14_monitor_replay tools/replay.cpp)
target_link_libraries(pcs14_monitor_replay PRIVATE pcs14_monitor)
if(Python3_FOUND)
  add_test(NAME monitor_matches_reference
    COMMAND ${Python3_EXECUTABLE} ${CMAKE_CURRENT_SOURCE_DIR}/tests/check_triggers.py
            $<TARGET_FILE:pcs14_monitor_replay>)
endif()
endif()
