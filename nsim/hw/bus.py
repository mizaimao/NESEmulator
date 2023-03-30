"""Bus implementation."""

from typing import Tuple, List

import numpy as np


RAM_RANGE: Tuple[int, int] = (0x00, 0xFFFF)


class Bus6502:
    def __init__(
        self,
    ):
        # add RAM
        mem_size: int = RAM_RANGE[1] - RAM_RANGE[0] + 1
        # np array with specified dtype notifies overflow
        self.ram: np.ndarray = np.full((mem_size,), 0x00, dtype=np.uint8)

    def read(self, addr: int, readonly: bool = False) -> int:
        """Read a 2-byte address and return a single byte value."""
        if RAM_RANGE[0] <= addr <= RAM_RANGE[1]:
            data: int = self.ram[addr]
        return data

    def write(self, addr: int, data: int):
        """Write a byte of data to a 2-byte addr."""
        if RAM_RANGE[0] <= addr <= RAM_RANGE[1]:
            self.ram[addr] = data
