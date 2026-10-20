# The core: everything that decides anything, with no hardware in it.
add_library(pcs14_core STATIC
  src/airframe_file.cpp
  src/attitude.cpp
  src/flight.cpp
  src/log_topics.cpp
  src/mixer.cpp
  src/rate.cpp
  src/ulog.cpp
)
target_include_directories(pcs14_core PUBLIC include)

# The host tests, with doctest (MIT), fetched at a pinned release
include(FetchContent)
FetchContent_Declare(doctest
  URL https://github.com/doctest/doctest/archive/refs/tags/v2.4.11.tar.gz
  URL_HASH SHA256=632ed2c05a7f53fa961381497bf8069093f0d6628c5f26286161fbd32a560186
  DOWNLOAD_EXTRACT_TIMESTAMP TRUE
)
FetchContent_MakeAvailable(doctest)

add_executable(pcs14_core_tests
  tests/main.cpp
  tests/test_math.cpp
  tests/test_attitude.cpp
  tests/test_rate.cpp
  tests/test_mixer.cpp
  tests/test_flight.cpp
  tests/test_ulog.cpp
)
target_link_libraries(pcs14_core_tests PRIVATE pcs14_core doctest::doctest)
add_test(NAME core COMMAND pcs14_core_tests)
set_tests_properties(core PROPERTIES FIXTURES_SETUP ulog_sample)

# pyulog, the library the flight sim's graders use, reads the sample log the tests wrote back,
# wherever it's installed for the Python CMake finds (pass -DPython3_EXECUTABLE to pick one)
find_package(Python3 COMPONENTS Interpreter)
if(Python3_FOUND)
  execute_process(COMMAND ${Python3_EXECUTABLE} -c "import pyulog"
    RESULT_VARIABLE pyulog_missing OUTPUT_QUIET ERROR_QUIET)
  if(pyulog_missing EQUAL 0)
    add_test(NAME ulog_reads_back
      COMMAND ${Python3_EXECUTABLE} ${CMAKE_CURRENT_SOURCE_DIR}/tests/check_ulog.py ulog_sample.ulg)
    set_tests_properties(ulog_reads_back PROPERTIES FIXTURES_REQUIRED ulog_sample)
  else()
    message(STATUS "no pyulog for ${Python3_EXECUTABLE}: the ULog read-back check is skipped")
  endif()
endif()
