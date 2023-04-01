"""PPU implementation."""

from typing import Dict, Tuple

import numpy as np

from nsim.hw.cartridge import Cartridge
from nsim.hw.colors import nes_colors


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

        # storage for all possible colors on NES
        self.dp_colors: Dict[int, Tuple[int, int, int]] = nes_colors

        # storage for main scene
        self.dp_screen: np.ndarray = np.full((240, 256, 4), 0x00, dtype=np.uint8)

        # storage for both name tables
        self.dp_nametb: np.ndarray = np.full((2, 240, 256, 3), 0x00, dtype=np.uint8)

        # storage for both pattern tables
        self.dp_pattern: np.ndarray = np.full((2, 128, 128, 3), 0x00, dtype=np.uint8)

        # debugging variable, marks if a screen rendering is complete
        self.frame_complete: bool = False
        self.scanline: int = 0  # int8, which row on screen
        self.cycle: int = 0  # int8, which column of screen
        self.rng: np.random.Generator = np.random.default_rng(seed=42)

    def get_screen(self) -> np.ndarray:
        """Debugging: Get an image for display."""
        return np.flip(self.dp_screen, axis=0)

    def get_name_table(self, index: int) -> np.ndarray:
        """Debugging: Get name table for display."""
        return self.dp_nametb[index]

    def get_pattern_table(self, index: int) -> np.ndarray:
        """Debugging: Get pattern table for display."""
        return self.dp_pattern[index]

    def clock(self):
        """The clock never stops. (???)"""
        # DEBUGGING USE
        _a: int = self.rng.integers(2)
        self.dp_screen[self.scanline, self.cycle - 1] = self.dp_colors[0x3E if _a else 0x30]
        ############

        self.cycle += 1
        # the following hardcoded numbers are decided based on hardware limits of NES
        if self.cycle >= 341:
            self.cycle = 0
            self.scanline += 1
            if self.scanline >= 261:
                self.scanline = -1
                self.frame_complete = True

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
