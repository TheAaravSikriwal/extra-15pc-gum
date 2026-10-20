// Starting the STM32H743: the vector table and the reset handler. GPL-3.0.
//
// The reset handler copies the initialized data from flash, clears the rest, turns on the FPU,
// runs the C++ constructors and calls main. Every interrupt this doesn't handle yet lands in
// an endless loop, where the hardware watchdog then resets the board: a hung processor means
// the motors stop, because the DShot frames stop with it.
#include <cstdint>

extern "C" {
extern uint32_t _sidata, _sdata, _edata, _sbss, _ebss, _estack;
extern void (*__init_array_start[])();
extern void (*__init_array_end[])();
int main();
void reset_handler();
void default_handler();
}

extern "C" void default_handler() {
  while (true) {
  }
}

extern "C" void reset_handler() {
  for (uint32_t *src = &_sidata, *dst = &_sdata; dst < &_edata;) *dst++ = *src++;
  for (uint32_t* dst = &_sbss; dst < &_ebss;) *dst++ = 0;
  // the FPU: full access to coprocessors 10 and 11 (CPACR, in the System Control Block)
  volatile uint32_t* const cpacr = reinterpret_cast<volatile uint32_t*>(0xE000ED88);
  *cpacr |= (0xFu << 20);
  __asm volatile("dsb\n isb");
  for (auto f = __init_array_start; f < __init_array_end; ++f) (*f)();
  main();
  default_handler();
}

// the Cortex-M7's own 16 entries; the STM32H743's 150 peripheral ones all go to the default
// until their drivers come
using Handler = void (*)();
struct VectorTable {
  uint32_t* stack;
  Handler core[15];
  Handler peripheral[150];
};

// built at compile time: the table has to be in flash at power-on, not filled in by code
constexpr VectorTable make_vectors() {
  VectorTable v{};
  v.stack = &_estack;
  v.core[0] = reset_handler;
  for (int k = 1; k < 15; ++k) v.core[k] = default_handler;
  for (int k = 0; k < 150; ++k) v.peripheral[k] = default_handler;
  return v;
}

__attribute__((section(".isr_vector"), used)) constexpr VectorTable kVectors = make_vectors();
