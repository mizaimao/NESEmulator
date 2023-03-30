"""
Bus implementation.

The original NES has 2KB (0x07FF) of ram, but we declare 8KB. This is because
nes uses RAM mirroring, with three copies mapped to the 2KB physical RAM.
Therefore, a value in RAM has four addresses to access to.

┌─────────┐   ┌─────────┐   ┌─────────┐   ┌─────────┐   ┌─────────┐              
│  6502   │   │   RAM   │   │         │   │         │   │         │              
│   CPU   │   │ 0x0000  │   │   APU   │   │CONTROLS │   │ OTHERS  │              
│         │   │ 0x1FFF  │   │         │   │         │   │         │              
└────┬────┘   └────┬────┘   └────┬────┘   └────┬────┘   └────┬────┘              
     │             │             │             │             │                   
     │             │             │             │             │                   
     └──┬──────────┴─────────────┴─────────────┴──────┬──────┴───────┬───CPU BUS
        │                                             │              │           
        │      ┌─ ── ── ── ── ── ── ── ── ── ── ── ── ┼─ ── ── ── ── ┼─ ── ─┐    
        │      │                         CARTRIDGE    │              │           
        │        ┌──────────────┐  ┌──────────────────┴───────┐  ┌───┴────┐ │    
        │      │ │   PATTERN    │  │       PROGRAM ROM        │  │ MAPPER │ │    
        │      │ │    0x0000    │  │          0x4020          │  │  R/W   │      
        │        │    0x1FFF    │  │          0xFFFF          │  │        │ │    
        │      │ └──────┬───────┘  └──────────────────────────┘  └────────┘ │    
        │      └ ── ── ─┼ ── ── ── ── ── ── ── ── ── ── ── ── ── ── ── ── ──     
        │               │                                                        
   ┌────┴────┐          │                                                        
   │         │          │                                                        
   │   PPU   ├──────────┴─────────┬─────────────────────────┬────PPU BUS         
   │         │                    │                         │                    
   └─────────┘            ┌───────┴──────┐          ┌───────┴──────┐             
                          │  NAME TABLE  │          │   PALETTES   │             
                          │    0x2000    │          │    0x3F00    │             
                          │    0x2FFF    │          │    0x3FFF    │             
                          └──────────────┘          └──────────────┘             

"""

from typing import Tuple, List

import numpy as np

from nsim.hw.cpu import SY6502
from nsim.hw.ppu import Visual2C02



RAM_RANGE: Tuple[int, int] = (0x0000, 0xFFFF)


class Bus6502:
    def __init__(
        self,
    ):
        # add cpu to the bus
        self.cpu: SY6502 = SY6502(ram_range=RAM_RANGE)
        # map cpu memory
        self.cpu_ram: np.ndarray = self.cpu.cpu_ram
        

    def cpu_read(self, addr: int, readonly: bool = False) -> int:
        """Read a 2-byte address and return a single byte value."""
        data: int = self.cpu.read(addr=addr, readonly=readonly)
        return data

    def cpu_write(self, addr: int, data: int):
        """Write a byte of data to a 2-byte addr."""
        self.cpu.write(addr=addr, data=data)

