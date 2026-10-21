# The ARK FPV layer (STM32H743): its drivers' logic, which builds and tests on the host like the
# core, and the image for the board itself when cross-compiling (cmake/arm-none-eabi.cmake).
include(FetchContent)
# libcanard (MIT, DroneCAN's fork): CAN frames and transfers for the GPS and the CAN nodes. Its
# own CMakeLists builds its tests, so only the sources are used (SOURCE_SUBDIR points nowhere).
FetchContent_Declare(libcanard
  URL https://github.com/dronecan/libcanard/archive/601ed35467e0ac38819df17cd7c918de19f62d58.tar.gz
  URL_HASH SHA256=d485a635e257182a5d34ecc1858a823c9b391a78a22760d80abb973fc60ff304
  SOURCE_SUBDIR none
  DOWNLOAD_EXTRACT_TIMESTAMP TRUE
)
# FatFs R0.16 (ChaN's 1-clause BSD license): the SD card's file system, for the flight logs
FetchContent_Declare(fatfs
  URL http://elm-chan.org/fsw/ff/arc/ff16.zip
  URL_HASH SHA256=99f7dc1f7e095356e4a9e3dbe29959090d8b948afe2bbc5441e52fdf4b85449e
  SOURCE_SUBDIR none
  DOWNLOAD_EXTRACT_TIMESTAMP TRUE
)
FetchContent_MakeAvailable(libcanard fatfs)

add_library(canard STATIC ${libcanard_SOURCE_DIR}/canard.c)
target_include_directories(canard SYSTEM PUBLIC ${libcanard_SOURCE_DIR})
target_compile_options(canard PRIVATE -w)  # not my code, and not written for these warnings

# FatFs reads its settings from the ffconf.h next to ff.c, so ff.c, ff.h and diskio.h are copied
# beside one carrying my changes to the released one: formatting on (the tests make RAM disks),
# the US code page instead of Japanese, and no clock on the board
set(fatfs_dir ${CMAKE_CURRENT_BINARY_DIR}/fatfs)
file(READ ${fatfs_SOURCE_DIR}/source/ffconf.h conf)
foreach(change "FF_USE_MKFS		0;FF_USE_MKFS		1" "FF_CODE_PAGE	932;FF_CODE_PAGE	437"
               "FF_FS_NORTC		0;FF_FS_NORTC		1" "FF_NORTC_YEAR	2025;FF_NORTC_YEAR	2026")
  list(GET change 0 from)
  list(GET change 1 to)
  string(FIND "${conf}" "#define ${from}" at)
  if(at EQUAL -1)
    message(FATAL_ERROR "FatFs's ffconf.h has no '#define ${from}': check the settings against it")
  endif()
  string(REPLACE "#define ${from}" "#define ${to}" conf "${conf}")
endforeach()
file(WRITE ${fatfs_dir}/ffconf.h "${conf}")
foreach(name ff.c ff.h diskio.h)
  configure_file(${fatfs_SOURCE_DIR}/source/${name} ${fatfs_dir}/${name} COPYONLY)
endforeach()
add_library(fatfs STATIC ${fatfs_dir}/ff.c)
target_include_directories(fatfs SYSTEM PUBLIC ${fatfs_dir})
target_compile_options(fatfs PRIVATE -w)

add_library(pcs14_h743_logic STATIC src/bmp388.cpp src/crsf.cpp src/dronecan.cpp src/dshot.cpp
            src/iim42653.cpp src/iis2mdc.cpp src/iwdg.cpp src/sdlog.cpp)
target_link_libraries(pcs14_h743_logic PUBLIC pcs14_core canard fatfs)
target_include_directories(pcs14_h743_logic PUBLIC include)

if(NOT CMAKE_CROSSCOMPILING)
  add_executable(pcs14_h743_tests ../core/tests/main.cpp tests/test_h743.cpp tests/test_iim42653.cpp
                 tests/test_clock.cpp tests/test_iwdg.cpp tests/test_i2c_sensors.cpp
                 tests/test_dronecan.cpp tests/test_sdlog.cpp)
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
