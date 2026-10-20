/* The STM32H743's memory, for the flight firmware on the ARK FPV. GPL-3.0.
 *
 * The image starts 128 KB into the flash, after the bootloader the board ships with (PX4's,
 * as on every ARK FPV), so it can be loaded over USB without a debugger. The stack and the
 * fast data live in the DTCM, the zero-wait-state RAM next to the core; the rest of the data
 * in the AXI SRAM. From RM0433, ST's reference manual for the STM32H743. */

ENTRY(reset_handler)

MEMORY
{
  FLASH (rx)  : ORIGIN = 0x08020000, LENGTH = 1920K
  DTCM  (rwx) : ORIGIN = 0x20000000, LENGTH = 128K
  AXI   (rwx) : ORIGIN = 0x24000000, LENGTH = 512K
}

_estack = ORIGIN(DTCM) + LENGTH(DTCM);

SECTIONS
{
  .isr_vector : { KEEP(*(.isr_vector)) } > FLASH

  .text :
  {
    *(.text*)
    *(.rodata*)
    . = ALIGN(4);
    __init_array_start = .;
    KEEP(*(.init_array*))
    __init_array_end = .;
    . = ALIGN(4);
  } > FLASH

  .ARM.exidx : { *(.ARM.exidx*) } > FLASH

  _sidata = LOADADDR(.data);
  .data :
  {
    . = ALIGN(4);
    _sdata = .;
    *(.data*)
    . = ALIGN(4);
    _edata = .;
  } > AXI AT> FLASH

  .bss (NOLOAD) :
  {
    . = ALIGN(4);
    _sbss = .;
    *(.bss*)
    *(COMMON)
    . = ALIGN(4);
    _ebss = .;
    end = .;   /* the heap starts here, for newlib's malloc */
    _end = .;
  } > AXI
}
