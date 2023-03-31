"""PPU implementation."""

from typing import Tuple

import numpy as np

class Visual2C02:
    """PPU of NES."""
    def __init__(self, cpu_ram: np.ndarray, ppu_ram: np.ndarray):
        # map memory devices
        self.cpu_ram: np.ndarray = cpu_ram
        self.ppu_ram: np.ndarray = ppu_ram
        

    def cpu_read(self, addr: int, readonly: bool = False) -> int:
        """Read a 2-byte address and return a single byte value.
        CPU can only address 8 address on ppu.
        """
        if addr == 0x0000:
            pass
        if addr == 0x0001:
            pass
        if addr == 0x0002:
            pass
        if addr == 0x0003:
            pass
        if addr == 0x0004:
            pass
        if addr == 0x0005:
            pass
        if addr == 0x0006:
            pass
        if addr == 0x0007:
            pass

    def cpu_write(self, addr: int, data: int):
        """Write a byte of data to a 2-byte addr.
        CPU can only address 8 address on ppu.
        """
        if addr == 0x0000:
            pass
        if addr == 0x0001:
            pass
        if addr == 0x0002:
            pass
        if addr == 0x0003:
            pass
        if addr == 0x0004:
            pass
        if addr == 0x0005:
            pass
        if addr == 0x0006:
            pass
        if addr == 0x0007:
            pass

    def ppu_read(self, addr: int, readonly: bool = False) -> int:
        """Read a 2-byte address and return a single byte value."""
        if 0x2000 <= addr <= 0x3FFF:
            data: int = self.ppu_ram[addr & 0x0007]  # ram mirror IO
            
        return data

    def ppu_write(self, addr: int, data: int):
        """Write a byte of data to a 2-byte addr."""
        if 0x2000 <= addr <= 0x3FFF:
            self.ppu_ram[addr & 0x0007] = data
            