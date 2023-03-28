"""Bus implementation."""

from typing import Tuple

class Bus6502:
    def __init__(
        self,
        range: Tuple[int, int] = (0x00, 0xFFFF),
    ):
        assert range[1] > range[0] > 0, f"Invalid bus range {range}."
        self.range: Tuple[int, int] = range
        pass

    def read(address: int, readonly: bool = False) -> int:
        """Read a 2-byte address and return a single byte value."""

        return
    
    def write(address: int, data: int):
        """Write a byte of data to a 2-byte address."""
        return