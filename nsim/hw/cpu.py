"""
CPU implementation.

  ┌───────────────────┐ ┌──────────────┐ ┌──────────────┐ ┌──────────────┐   
  │       6502        │ │     RAM      │ │     DEV1     │ │     DEV2     │   
  │        CPU        │ │    2048KB    │ │ $4000-$4FFF  │ │ $A000-$BFFF  │   
  │                   │ │ $0000-$07FF  │ │              │ │              │   
  └──┬──────▲──────┬──┘ └─────┬─▲──────┘ └──────┬───────┘ └──────▲───────┘   
     │      │      │          │ │               │                │           
     │      │      │          │ │               │                │           
 Address  Data   State        │ │ R/W           │ R/O            │ W/O       
     │      │      │          │ │               │                │           
     │      │      │          │ │               │                │           
  ┌──▼──────▼──────▼──────────▼─┴───────────────▼────────────────┴──────────┐
  │                               16-bit bus                                │
  │                              (64KB range)                               │
  └─────────────────────────────────────────────────────────────────────────┘

The CPU communicates with the BUS with three types of signals:
1. Address; 2. Data; 3. State (whether it's reading or writing).

Devices connected to the bus is sensitive to the address that CPU gives and
depending on the type of state the CPU outputs, the device will return a value
or write one from "Data" that CPU gives.

Certain devices are read-only or write-only and therefore have to deal with
invalid operations (or just ignore?).
"""
from dataclasses import dataclass

from nsim.hw.bus import Bus6502


@dataclass
class FLAGS6502:
    """Flags in 6502 processor."""

    C: int = 1 << 0  # carry bit
    Z: int = 1 << 1  # zero
    I: int = 1 << 2  # disable interrupts
    D: int = 1 << 3  # decimal mode (disabled in this implementation, as does nes)
    B: int = 1 << 4  # break
    U: int = 1 << 5  # unused
    V: int = 1 << 6  # overflow
    N: int = 1 << 7  # negative (used when using signed variables)


class SY6502:
    def __init__(self):
        # connect to the bus, which allocates ram
        self.bus: Bus6502 = Bus6502()
        # setup flags
        self.flags: FLAGS6502 = FLAGS6502()
        # setup registers
        self.a: int = 0x00  # accumulator register
        self.x: int = 0x00  # X register
        self.y: int = 0x00  # Y register
        self.stkp: int = 0x00  # stack pointer
        self.pc: int = 0x00  # program counter
        self.status: int = 0x00  # status register

    def read(self, addr: int, readonly: bool = False) -> int:
        """Read a 2-byte address and return a single byte value."""
        data: int = self.bus.read(addr=addr, readonly=readonly)
        return data

    def write(self, addr: int, data: int):
        """Write a byte of data to a 2-byte addr."""
        self.bus.write(addr=addr, data=data)

    def read_flag():
        """Read a specific flag value."""

    def set_flag():
        """Overwrite a flag value."""

    def IMP() -> int:
        """Addressing mode."""

    def IMM() -> int:
        """Addressing mode."""

    def ZP0() -> int:
        """Addressing mode."""

    def ZPX() -> int:
        """Addressing mode."""

    def ZPY() -> int:
        """Addressing mode."""

    def REL() -> int:
        """Addressing mode."""

    def ABS() -> int:
        """Addressing mode."""

    def ABX() -> int:
        """Addressing mode."""

    def ABY() -> int:
        """Addressing mode."""

    def IND() -> int:
        """Addressing mode."""

    def IZX() -> int:
        """Addressing mode."""

    def IZY() -> int:
        """Addressing mode."""
