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
from pathlib import Path

import numpy as np

from nsim.hw.cpu import SY6502
from nsim.hw.ppu import Visual2C02
from nsim.hw.cartridge import Cartridge


class Bus6502:
    def __init__(self, cartridge_path: Path = None):
        """The referenced design uses bus as the sole target to read and write.
        But because that Python cannot import in a loop manner, We have to
        create individual memory devices and share them between different
        objects, and perform R/W there."""
        # setup memories
        # np array with specified dtype notifies overflow
        self.cpu_ram: np.ndarray = np.full((0x1FFF - 0x0000 + 1,), 0x00, dtype=np.uint8)
        self.ppu_ram: np.ndarray = np.full((0x3FFF - 0x2000 + 1,), 0x00, dtype=np.uint8)

        # setup cartridge
        self.cart: Cartridge = Cartridge(
            cpu_ram=self.cpu_ram, ppu_ram=self.ppu_ram, cart_path=cartridge_path
        )

        # add cpu to the bus
        self.cpu: SY6502 = SY6502(cpu_ram=self.cpu_ram, ppu_ram=self.ppu_ram)
        # add ppu
        self.ppu: Visual2C02 = Visual2C02(
            cpu_ram=self.cpu_ram,
            ppu_ram=self.ppu_ram,
        )

        # variable logs how many times clock function has been called
        self.clock_counter: int = 0
        self.__post_init__()

    def __post_init__(self):
        self.cpu.inject_parent_functions(
            read_function=self.cpu_read, write_function=self.cpu_write
        )

    def insert_cartridge(self):
        """Emulates cartridge insertion."""
        self.ppu.insert_cartridge(cart=self.cart)

    def reset(self):
        """Reset button on NES."""
        self.cpu.reset()
        self.clock_counter = 0
        self.cpu_ram[:] = 0x00
        self.ppu_ram[:] = 0x00
        self.cpu.reload_memory(cpu_ram=self.cpu_ram, ppu_ram=self.ppu_ram)
        self.ppu.reload_memory(cpu_ram=self.cpu_ram, ppu_ram=self.ppu_ram)

    def clock(self):
        """Provides system clock ticks."""
        self.ppu.clock()
        # PPU is clocked three times as CPU
        if self.clock_counter % 3 == 0:
            self.cpu.clock()
        self.clock_counter += 1

    def cpu_read(self, addr: int, readonly: bool = False) -> int:
        data: int = 0x00
        # if self.cart.cpu_read(addr=addr):
        #     pass
        if 0x0000 <= addr <= 0x1FFF:
            data = self.cpu_ram[addr & 0x07FF]  # ram mirror IO
        elif 0x2000 <= addr <= 0x3FFF:
            data = self.ppu.cpu_read(addr=(addr & 0x0007))
        return data

    def cpu_write(self, addr: int, data: int):
        # write with cartridge first, and that function will return if the
        # operation was successful
        # if self.cart.cpu_write(addr=addr, data=data):
        #     pass
        if 0x0000 <= addr <= 0x1FFF:
            self.cpu_ram[addr & 0x07FF] = data
        elif 0x2000 <= addr <= 0x3FFF:
            self.ppu.cpu_write(addr=(addr & 0x0007), data=data)
