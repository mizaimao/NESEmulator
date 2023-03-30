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



RAM_RANGE: Tuple[int, int] = (0x0000, 0xFFFF)


class Bus6502:
    def __init__(
        self,
    ):
        # add RAM
        mem_size: int = RAM_RANGE[1] - RAM_RANGE[0] + 1
        # np array with specified dtype notifies overflow
        self.cpu_ram: np.ndarray = np.full((mem_size,), 0x00, dtype=np.uint8)

    def cpu_read(self, addr: int, readonly: bool = False) -> int:
        """Read a 2-byte address and return a single byte value."""
        if RAM_RANGE[0] <= addr <= RAM_RANGE[1]:
            data: int = self.cpu_ram[addr]
        return data

    def cpu_write(self, addr: int, data: int):
        """Write a byte of data to a 2-byte addr."""
        if RAM_RANGE[0] <= addr <= RAM_RANGE[1]:
            self.cpu_ram[addr] = data
