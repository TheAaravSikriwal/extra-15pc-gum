# The core: everything that decides anything, with no hardware in it.
add_library(pcs14_core STATIC
  src/attitude.cpp
  src/mixer.cpp
  src/rate.cpp
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
)
target_link_libraries(pcs14_core_tests PRIVATE pcs14_core doctest::doctest)
add_test(NAME core COMMAND pcs14_core_tests)
