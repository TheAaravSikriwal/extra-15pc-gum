# Cross-compiling for the ARK FPV's STM32H743 (Cortex-M7, double-precision FPU), with the GNU
# Arm toolchain (Ubuntu's gcc-arm-none-eabi, and newlib-nano):
#   cmake -S firmware -B build/h743 -DCMAKE_TOOLCHAIN_FILE=firmware/cmake/arm-none-eabi.cmake
set(CMAKE_SYSTEM_NAME Generic)
set(CMAKE_SYSTEM_PROCESSOR arm)
set(CMAKE_C_COMPILER arm-none-eabi-gcc)
set(CMAKE_CXX_COMPILER arm-none-eabi-g++)
set(CMAKE_ASM_COMPILER arm-none-eabi-gcc)
set(CMAKE_TRY_COMPILE_TARGET_TYPE STATIC_LIBRARY)

set(PCS14_CPU "-mcpu=cortex-m7 -mthumb -mfpu=fpv5-d16 -mfloat-abi=hard")
set(CMAKE_C_FLAGS_INIT "${PCS14_CPU} -ffunction-sections -fdata-sections")
set(CMAKE_CXX_FLAGS_INIT "${PCS14_CPU} -ffunction-sections -fdata-sections -fno-exceptions -fno-rtti -fno-threadsafe-statics")
set(CMAKE_EXE_LINKER_FLAGS_INIT "${PCS14_CPU} --specs=nano.specs --specs=nosys.specs -Wl,--gc-sections")

set(PCS14_SANITIZE OFF CACHE BOOL "" FORCE)  # no sanitizers on a microcontroller
set(PCS14_SITL OFF CACHE BOOL "" FORCE)
