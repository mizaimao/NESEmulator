"""Mapper implementation."""
from typing import Union
from abc import ABC, abstractclassmethod


class Mapper(ABC):
    def __init__(
        self,
        prg_banks: int,
        chr_banks: int,
    ):
        self.prg_banks: int = prg_banks
        self.chr_banks: int = chr_banks

    # takes in addresses cpu/ppu requested and translate them into addresses
    # on the cartridge. If the address is successfully mapped, True is returned
    @abstractclassmethod
    def cpu_map_read(self, addr: int, mapped: int) -> bool:  # uint16 and uint32
        pass

    @abstractclassmethod
    def cpu_map_write(self, addr: int, mapped: int) -> bool:  # uint16 and uint32
        pass

    @abstractclassmethod
    def ppu_map_read(self, addr: int, mapped: int) -> bool:  # uint16 and uint32
        pass

    @abstractclassmethod
    def ppu_map_write(self, addr: int, mapped: int) -> bool:  # uint16 and uint32
        pass


class Mapper000(Mapper):
    def __init__(self, prg_banks: int, chr_banks: int):
        super().__init__(prg_banks, chr_banks)

    def cpu_map_read(self, addr: int) -> Union[int, None]:  # uint16 and uint32
        """Return the mapped location."""
        if 0x8000 <= addr <= 0xFFFF:
            return addr & (0x7FFF if self.prg_banks > 1 else 0x3FFF)
        return None

    def cpu_map_write(self, addr: int) -> Union[int, None]:  # uint16 and uint32
        if 0x8000 <= addr <= 0xFFFF:
            return addr & (0x7FFF if self.prg_banks > 1 else 0x3FFF)
        return None

    def ppu_map_read(self, addr: int) -> Union[int, None]:  # uint16 and uint32
        if 0x8000 <= addr <= 0x1FFF:
            return addr
        return None

    def ppu_map_write(self, addr: int, mapped: int) -> bool:  # uint16 and uint32
        """PPU won't be able to write to a read-only memory, and therefore nothing
        will happen."""
        return False
