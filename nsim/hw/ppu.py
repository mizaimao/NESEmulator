"""PPU implementation."""

from typing import Tuple

import numpy as np

from nsim.hw.cartridge import Cartridge


class Visual2C02:
    """PPU of NES."""

    def __init__(self, cpu_ram: np.ndarray, ppu_ram: np.ndarray):
        # map memory devices
        self.cpu_ram: np.ndarray = cpu_ram
        self.ppu_ram: np.ndarray = ppu_ram
        self.cart: Cartridge = None

        # vram device, holding name table info
        # NES has a 2KB vram; one name table has 1KB so we split it into two
        # parts, as NES has capability to store two name tables.
        # It may hold 4 name tables with some tricks (TODO)
        self.name_table: np.ndarray = np.full(
            (2, 1024 - 0x0000 + 1), 0x00, dtype=np.uint8
        )
        # palette storage
        self.palette: np.ndarray = np.full((32,), 0x00, dtype=np.uint8)

        # pattern memory (only for MODs)
        # This memory exists on normal cartridge systems
        # This can be removed if no self-written mapper is developed;
        # it will not affect at all any cartridges
        self.pattern: np.ndarray = np.full((2, 4096), 0x00, dtype=np.uint8)

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

    def reload_memory(self, cpu_ram: np.ndarray, ppu_ram: np.ndarray):
        self.cpu_ram = cpu_ram
        self.ppu_ram = ppu_ram

    def insert_cartridge(self, cart: Cartridge):
        """Emulates cartridge insertion."""
        self.cart = cart

    def clock(self):
        """Provides PPU clock ticks."""
        self.clock_counter += 1
