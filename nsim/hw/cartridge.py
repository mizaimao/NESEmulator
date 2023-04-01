"""
Cartridge implementation.

┌─  ──  ──  ──  ──  ──  ──  ──  ──  ──  ──  ──  ──                  
│                                                  │                
│  ┌───────┐  ┌───────┐            ┌──────────┐    │                
   │       │  │       │            │          │          ┌─────────┐
   │       │  │       │            │          │          │         │
│  │ BANK0 │  │ BANK1 │   ┌────────┤─ ─ ─ ─ ─ ┤◀─DATA───▶│         │
│  │       │  │       │   │        │          │    │     │   CPU   │
   │       │  │       │   │        │          │          │         │
   │       │  │       │   │        │          │◀─ADDR────┤         │
│  └───┬───┘  └───┬───┘   │        │          │    │     │         │
│      │          │       │        │          │    │     └─────────┘
       └──────────┴───────┘        │          │                     
                                   │  MAPPER  │                     
│   ┌─────────────────┐            │          │    │     ┌─────────┐
│   │     LEVEL1      ├─────┐      │          │    │     │         │
    ├─────────────────┤     ├──────┤─ ─ ─ ─ ─ ┤◀──DATA──▶│         │
    │     LEVEL2      ├─────┤      │          │          │   PPU   │
│   ├─────────────────┤     │      │          │    │     │         │
│   │     LEVEL3      ├─────┤      │          │◀──ADDR───┤         │
    ├─────────────────┤     │      │          │          │         │
    │     LEVEL4      ├─────┘      │          │          └─────────┘
│   └─────────────────┘            │          │    │                
│                                  └──────────┘    │                
                                                                    
 ──  ──  ──  ──  ──  ──  ──  ──  ──  ──  ──  ──  ──    

    The majority of the pins on a cartridge are just data pins and address pins
connected to CPU and PPU.
It has program memory, and pattern memory (where sprites are stored).
The cartridge may contain on-board memory chips that are larger than
addressable range of CPU/PPU. A mapper is then used to resolve this.
When CPU/PPU requests data for an address, the mapper may retrieve the data
from different physical locations on board (and therefore different
returned values). An example is on data used on different levels.

The CPU configures the mapper, and the mapper translates the address to
on-board ones. A mapper is a physical construction.
"""


from typing import Dict, Tuple, Union
from dataclasses import dataclass
from pathlib import Path

import numpy as np

from nsim.hw.mapper import Mapper, Mapper000

mappers: Dict[int, Mapper] = {0: Mapper000}


@dataclass
class CartHeader:
    """
    Header of NES file (*.ines). The header is of 16 bytes.
    https://www.nesdev.org/wiki/INES
    """

    # byte 0-3, 4-byte constant name in ASCII "NES" plus a MS-DOS EOF
    name: str
    # byte 4, size of program ROM in 16 KB units
    prg_rom_chunks: int  # 8-bit
    # byte 5, size of CHR ROM in 8 KB units; 0 means cart uses CHR RAM
    chr_rom_chunks: int  # 8-bit
    # byte 6: Flags 6 – Mapper, mirroring, battery, trainer
    #    76543210
    #    ||||||||
    #    |||||||+- Mirroring: 0: horizontal (vertical arrangement) (CIRAM A10 = PPU A11)
    #    |||||||              1: vertical (horizontal arrangement) (CIRAM A10 = PPU A10)
    #    ||||||+-- 1: Cartridge contains battery-backed PRG RAM ($6000-7FFF) or other persistent memory
    #    |||||+--- 1: 512-byte trainer at $7000-$71FF (stored before PRG data)
    #    ||||+---- 1: Ignore mirroring control or above mirroring bit; instead provide four-screen VRAM
    #    ++++----- Lower nybble of mapper number
    mapper1: int  # 8-bit
    # byte 7: Flags 7 – Mapper, VS/Playchoice, NES 2.0
    #   76543210
    #   ||||||||
    #   |||||||+- VS Unisystem
    #   ||||||+-- PlayChoice-10 (8 KB of Hint Screen data stored after CHR data)
    #   ||||++--- If equal to 2, flags 8-15 are in NES 2.0 format
    #   ++++----- Upper nybble of mapper number
    mapper2: int  # 8-bit
    # byte 8: Flags 8 – PRG-RAM size (rarely used extension)
    prg_ram_size: int  # 8-bit
    # byte 9: Flags 9 – TV system (rarely used extension), (0: NTSC; 1: PAL)
    tv_system1: int  # 8-bit
    # byte 10: Flags 10 – TV system, PRG-RAM presence (unofficial, rarely used extension)
    #   76543210
    #   ||  ||
    #   ||  ++- TV system (0: NTSC; 2: PAL; 1/3: dual compatible)
    #   |+----- PRG RAM ($6000-$7FFF) (0: present; 1: not present)
    #   +------ 0: Board has no bus conflicts; 1: Board has bus conflicts
    tv_system2: int  # 8-bit
    # byte 11-15: Unused padding (should be filled with zero, but some rippers put their name across bytes 7-15)
    unused: str  # length of five


class Cartridge:
    """Cartridge of NES."""

    def __init__(
        self, cpu_ram: np.ndarray, ppu_ram: np.ndarray, cart_path: Path = None
    ):
        # map memory devices
        self.cpu_ram: np.ndarray = cpu_ram
        self.ppu_ram: np.ndarray = ppu_ram

        self.n_mapper_id: int = 0  # how many mappers are we using
        self.n_prgbanks: int = 0  # how many respective banks there are
        self.n_chrbanks: int = 0

        self.prg_memory: np.ndarray = None
        self.chr_memory: np.ndarray = None
        self.mapper: Mapper = None

        # load cartridge
        self.load_cart(cart_path=cart_path)

    def cpu_read(self, addr: int) -> Union[int, None]:
        """Read a 2-byte address and return a single byte value."""
        # uint32 or None
        mapped: Union[int, None] = self.mapper.cpu_map_read(addr=addr)
        if mapped:
            return self.prg_memory[mapped]
        return None

    def cpu_write(self, addr: int, data: int) -> bool:
        """Write a byte of data to a 2-byte addr.
        Note return type indicates if writing is legal.
        """
        mapped: Union[int, None] = self.mapper.cpu_map_write(addr=addr)
        if mapped:
            self.prg_memory[mapped] = data
            return True
        return False

    def ppu_read(self, addr: int) -> Union[int, None]:
        """Read a 2-byte address and return a single byte value."""
        mapped: Union[int, None] = self.mapper.ppu_map_read(addr=addr)
        if mapped:
            return self.chr_memory[mapped]
        return None

    def ppu_write(self, addr: int, data: int) -> bool:
        """Write a byte of data to a 2-byte addr.
        Note return type indicates if writing is legal.
        PPU writes are illegal because they write to ROM.
        """
        return False

    def load_cart(self, cart_path: Union[Path, str] = None):
        """Load cartridge into numpy array."""
        if cart_path is None:
            print("No cartridge.")
            return

        cart_path: Path = Path(cart_path)
        if not cart_path.is_file():
            print(Path().resolve().parent, cart_path)
            cart_path = Path(__file__).parent.parent.joinpath(f"assets/{cart_path}")
            print(cart_path)
        if not cart_path.is_file():
            raise FileNotFoundError(
                f"File {cart_path} cannot be found at given location or in assets folder."
            )
        # now load cartridge
        with open(cart_path, "rb") as file:
            contents = file.read()
        # may raise other errors
        # load cart dump as a hex (8-bit unsigned) array
        cart: np.ndarray = np.array(list(contents), dtype=np.uint8)

        header_offset: int = 16  # header is of 16-byte size
        # load cartridge header
        header: CartHeader = Cartridge.load_header(cart=cart)
        # detect if a trainer is on board; it's a 512-byte space before program_rom
        trainer_present: bool = bool(header.mapper1 & 0x04)
        # there are three types of cartridges
        cart_type: int = ((header.mapper2 >> 4) << 4) | (header.mapper1 >> 4)

        if cart_type == 0:
            pass
        elif cart_type == 1:
            self.n_prgbanks = header.prg_rom_chunks
            # number times 16 KB chunks
            data_size: int = self.n_prgbanks * 16384
            # copy cartridge program data into class attribute
            start: int = header_offset + trainer_present * 512
            end: int = start + data_size
            self.prg_memory = cart[start:end].copy()
            start = end

            self.n_chrbanks = header.chr_rom_chunks
            # number times 8 KB chunks
            data_size = self.n_chrbanks * 8192
            end = start + data_size
            self.chr_memory = cart[start:end].copy()
        elif cart_type == 2:
            pass
        else:
            raise ValueError(f"Unknown cartridge type: {cart_type}.")

        self.n_mapper_id = ((header.mapper2 >> 4) << 4) | (header.mapper1 >> 4)
        self.mapper = mappers[self.n_mapper_id](
            prg_banks=self.n_prgbanks, chr_banks=self.n_chrbanks
        )

    @staticmethod
    def load_header(cart: np.ndarray) -> CartHeader:
        header: CartHeader = CartHeader(
            name=cart[0:4],
            prg_rom_chunks=cart[4],
            chr_rom_chunks=cart[5],
            mapper1=cart[6],
            mapper2=cart[7],
            prg_ram_size=cart[8],
            tv_system1=cart[9],
            tv_system2=cart[10],
            unused=cart[11:16],
        )
        return header
