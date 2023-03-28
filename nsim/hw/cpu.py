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

from nsim.hw.bus import Bus6502


class SY6502:
    def __init__(self):
        self.bus: Bus6502 = Bus6502()

    
    def read(self, addr: int, readonly: bool = False) -> int:
        """Read a 2-byte address and return a single byte value."""
        data: int = self.bus.read(addr=addr, readonly=readonly)
        return data

    def write(self, addr: int, data: int):
        """Write a byte of data to a 2-byte addr."""
        self.bus.write(addr=addr, data=data)
