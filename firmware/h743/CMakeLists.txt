# The ARK FPV layer (STM32H743): its drivers' logic, which builds and tests on the host like the
# core, and the image for the board itself when cross-compiling (cmake/arm-none-eabi.cmake).
add_library(pcs14_h743_logic STATIC src/bmp388.cpp src/crsf.cpp src/dshot.cpp src/iim42653.cpp
            src/iis2mdc.cpp src/iwdg.cpp)
target_link_libraries(pcs14_h743_logic PUBLIC pcs14_core)
target_include_directories(pcs14_h743_logic PUBLIC include)

if(NOT CMAKE_CROSSCOMPILING)
  add_executable(pcs14_h743_tests ../core/tests/main.cpp tests/test_h743.cpp tests/test_iim42653.cpp
                 tests/test_clock.cpp tests/test_iwdg.cpp tests/test_i2c_sensors.cpp)
  target_link_libraries(pcs14_h743_tests PRIVATE pcs14_h743_logic pcs14_monitor doctest::doctest)
  add_test(NAME h743 COMMAND pcs14_h743_tests)
endif()

# the image for the board: the vector table, the startup, the main loop and the linker script
if(CMAKE_CROSSCOMPILING)
  add_executable(pcs14_h743 board/startup.cpp board/main.cpp)
  target_link_libraries(pcs14_h743 PRIVATE pcs14_h743_logic pcs14_monitor)
  target_link_options(pcs14_h743 PRIVATE -T${CMAKE_CURRENT_SOURCE_DIR}/board/stm32h743.ld
                      -Wl,-Map=pcs14_h743.map)
  set_target_properties(pcs14_h743 PROPERTIES SUFFIX ".elf")
  add_custom_command(TARGET pcs14_h743 POST_BUILD COMMAND arm-none-eabi-size $<TARGET_FILE:pcs14_h743>)
endif()
