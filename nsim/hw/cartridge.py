"""Cartridge implementation."""

from typing import Tuple

import numpy as np

class Cartridge:
    """Cartridge of NES."""
    def __init__(self, cpu_ram: np.ndarray, ppu_ram: np.ndarray):
        # map memory devices
        self.cpu_ram: np.ndarray = cpu_ram
        self.ppu_ram: np.ndarray = ppu_ram
        

    def cpu_read(self, addr: int, readonly: bool = False) -> int:
        """Read a 2-byte address and return a single byte value.
        """

    def cpu_write(self, addr: int, data: int):
        """Write a byte of data to a 2-byte addr.
        """


    def ppu_read(self, addr: int, readonly: bool = False) -> int:
        """Read a 2-byte address and return a single byte value."""
        if 0x2000 <= addr <= 0x3FFF:
            data: int = self.ppu_ram[addr & 0x0007]  # ram mirror IO
            
        return data

    def ppu_write(self, addr: int, data: int):
        """Write a byte of data to a 2-byte addr."""
        if 0x2000 <= addr <= 0x3FFF:
            self.ppu_ram[addr & 0x0007] = data
