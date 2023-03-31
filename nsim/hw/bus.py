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
from nsim.hw.cartridge import Cartridge


class Bus6502:
    def __init__(
        self,
    ):
        """The referenced design uses bus as the sole target to read and write.
        But because that Python cannot import in a loop manner, We have to
        create individual memory devices and share them between different
        objects, and perform R/W there."""
        # setup memories
        # np array with specified dtype notifies overflow
        self.cpu_ram: np.ndarray = np.full((0x1FFF - 0x0000 + 1,), 0x00, dtype=np.uint8)
        self.ppu_ram: np.ndarray = np.full((0x3FFF - 0x2000 + 1,), 0x00, dtype=np.uint8)

        # setup cartridge
        self.cart_device: Cartridge = Cartridge(
            cpu_ram=self.cpu_ram, ppu_ram=self.ppu_ram
        )
        self.cart: Cartridge = None

        # add cpu to the bus
        self.cpu: SY6502 = SY6502(cpu_ram=self.cpu_ram, ppu_ram=self.ppu_ram)
        # add ppu
        self.ppu: Visual2C02 = Visual2C02(
            cpu_ram=self.cpu_ram,
            ppu_ram=self.ppu_ram,
        )

        # variable logs how many times clock function has been called
        self.clock_counter: int = 0

    def insert_cartridge(self):
        """Emulates cartridge insertion."""
        self.cart = self.cart_device
        self.ppu.insert_cartridge(cart=self.cart)

    def reset(self):
        """Reset button on NES."""
        self.cpu.reset()
        self.clock_counter = 0
        self.cpu.reload_memory(cpu_ram=self.cpu_ram, ppu_ram=self.ppu_ram)
        self.ppu.reload_memory(cpu_ram=self.cpu_ram, ppu_ram=self.ppu_ram)

    def clock(self):
        """Provides system clock ticks."""
        self.clock_counter += 1

    def bus_cpu_write(self, addr: int, data: int):
        # write with cartridge first, and that function will return if the
        # operation was successful
        if self.cart.cpu_write(addr=addr, data=data):
            pass
        elif 0x0000 <= addr <= 0x1FFF:
            self.cpu.cpu_write(addr=addr, data=data)
        elif 0x2000 <= addr <= 0x3FFF:
            self.ppu.cpu_write(addr=(addr & 0x0007), data=data)

    def bus_cpu_read(self, addr: int) -> int:
        if self.cart.cpu_read(addr=addr):
            pass
        elif 0x0000 <= addr <= 0x1FFF:
            data: int = self.cpu.cpu_read(addr=addr)
        elif 0x2000 <= addr <= 0x3FFF:
            data = self.ppu.cpu_read(addr=(addr & 0x0007))
        return data
