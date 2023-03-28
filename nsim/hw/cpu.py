"""
CPU implementation.

  ┌───────────────────┐ ┌──────────────┐ ┌──────────────┐ ┌──────────────┐   
  │       6502        │ │     RAM      │ │     DEV1     │ │     DEV2     │   
  │        CPU        │ │    2048KB    │ │ $4000-$4FFF  │ │ $A000-$BFFF  │   
  │                   │ │ $0000-$07FF  │ │              │ │              │   
  └──┬──────▲──────┬──┘ └─────┬─▲──────┘ └──────┬───────┘ └──────▲───────┘   
     │      │      │          │ │               │                │           
     │      │      │          │ │               │                │           
 Address  Data   State        │ │ R/W           │ R/O            │ W/O       
     │      │      │          │ │               │                │           
     │      │      │          │ │               │                │           
  ┌──▼──────▼──────▼──────────▼─┴───────────────▼────────────────┴──────────┐
  │                               16-bit bus                                │
  │                              (64KB range)                               │
  └─────────────────────────────────────────────────────────────────────────┘

The CPU communicates with the BUS with three types of signals:
1. Address; 2. Data; 3. State (whether it's reading or writing).

Devices connected to the bus is sensitive to the address that CPU gives and
depending on the type of state the CPU outputs, the device will return a value
or write one from "Data" that CPU gives.

Certain devices are read-only or write-only and therefore have to deal with
invalid operations (or just ignore?).
"""
from dataclasses import dataclass
from typing import Callable, Dict, List

from nsim.hw.bus import Bus6502


@dataclass
class FLAGS6502:
    """Flags in 6502 processor."""

    C: int = 1 << 0  # carry bit
    Z: int = 1 << 1  # zero
    I: int = 1 << 2  # disable interrupts
    D: int = 1 << 3  # decimal mode (disabled in this implementation, as does nes)
    B: int = 1 << 4  # break
    U: int = 1 << 5  # unused
    V: int = 1 << 6  # overflow
    N: int = 1 << 7  # negative (used when using signed variables)


class SY6502:
    @dataclass
    class Instruction:
        name: str
        opcode: Callable
        addrmode: Callable
        cycle: int = 0

    def __init__(self):
        # connect to the bus, which allocates ram
        self.bus: Bus6502 = Bus6502()
        # setup flags
        self.flags: FLAGS6502 = FLAGS6502()
        # setup registers
        self.a: int = 0x00  # accumulator register
        self.x: int = 0x00  # X register
        self.y: int = 0x00  # Y register
        self.stkp: int = 0x00  # stack pointer
        self.pc: int = 0x0000  # program counter, stores an address
        self.status: int = 0x00  # status register

        # variable to store fetched data from addressable locations
        self.fetched: int = 0x00
        # depending on the address mode, we may read data from different places
        # in memory, and we store that address here
        self.addr_abs: int = 0x0000  # 16-bit address
        # jump may occur, and in 6502 processor, this jump can only occur within
        # a certain range
        self.addr_rel: int = 0x00
        # opcode store
        self.opcode: int = 0x00
        # number of cycles left in this operation
        self.cycle: int = 0
        # generate instruction list
        self.instructions: List[self.Instruction] = self.create_instructions()

    def read(self, addr: int, readonly: bool = False) -> int:
        """Read a 2-byte address and return a single byte value."""
        data: int = self.bus.read(addr=addr, readonly=readonly)
        return data

    def write(self, addr: int, data: int):
        """Write a byte of data to a 2-byte addr."""
        self.bus.write(addr=addr, data=data)

    def read_flag():
        """Read a specific flag value."""

    def set_flag():
        """Overwrite a flag value."""

    def clock(self):
        """Clock function."""
        if self.cycle == 0:
            # read the next opcode, which is 1-byte
            opcode: int = self.read(addr=self.pc)
            # update address
            self.pc += 1

            # pointer to dataclass
            instruction: self.Instruction = self.instructions[opcode]

            # using this opcode to get required cycle count
            add_cycle: int = instruction.cycle
            # call the address mode function
            # will return 1 if it requires additional cycles or 0 if not
            add_cycle_address: int = instruction.addrmode()

            # call the operate function
            # will return 1 if it requires additional cycles or 0 if not
            add_cycle_operation: int = instruction.opcode()

            # if either operation or address mode requires additional cycles,
            # we add that to cycle count
            add_cycle += add_cycle_address & add_cycle_operation
            # update in-class variable
            self.cycle += add_cycle

        # decrease cycle count
        self.cycle -= 1

    def reset():
        """Reset signal. Interrupts the processor after current cycle."""

    def irq():
        """Interrupt request. Interrupts the processor after current cycle.
        May be ignored if flags disables this function.
        """

    def nmi():
        """Non-maskable interrupt request signal. Interrupts the processor after
        current cycle. This interrupt signal cannot be ignored.
        """

    def fetch(self):
        """Fetch data from addressable memory."""

    # addressing mode section (totally 12)
    # https://slark.me/c64-downloads/6502-addressing-modes.pdf
    def IMP(self) -> int:
        """Addressing mode.
        Implied/implicit. Means no data is parsed into instruction. It can also mean it
        operates on accumulator.
        Set fetched variable to content accumulator.
        """
        self.fetched = self.a
        return 0

    def IMM(self) -> int:
        """Addressing mode.
        Immediate addressing. Operand is the second byte of instruction. We
        therefore increase the counter and update cpu with that address.
        """
        self.pc += 1
        self.addr_abs = self.pc
        return 0

    def ZP0(self) -> int:
        """Addressing mode.
        Zero-page addressing. An address 0xAAEE can have a page referring to AA
        while EE is called offset. Zero-page addressing means the interested
        byte is located somewhere on the page 0, namely, its address should be
        like 0x00GG. 6502 programs tend to have the working memory located
        around 0, and thus it can require one less byte to operate (considering)
        operating on higher pages would require one additional byte. It
        functionally fetches a value with 8-bit address on page zero.
        """
        self.addr_abs = self.read(self.pc)
        self.pc += 1
        self.addr &= 0x00FF  # masking the page
        return 0

    def ZPX(self) -> int:
        """Addressing mode.
        Zero-page addressing with value in X register being used as offset.
        This can be used for accessing continuous region of memory, like an
        array. The retrieved value has an address, and the value in x register
        offsets that address.
        """
        self.addr_abs = self.read(self.pc) + self.x
        self.pc += 1
        self.addr_abs &= 0x00FF
        return 0

    def ZPY(self) -> int:
        """Addressing mode.
        Zero-page addressing with value in Y register being used as offset."""
        self.addr_abs = self.read(self.pc) + self.y
        self.pc += 1
        self.addr_abs &= 0x00FF
        return 0

    def REL(self) -> int:
        """Addressing mode."""

    def ABS(self) -> int:
        """Addressing mode.
        Absolute addressing. The second byte of instruction is the offset of the
        next effective address, and the third byte is the page. This forms a
        16-bit address location which has the full 64KB range."""
        lower: int = self.read(self.pc)  # load lower part
        self.pc += 1  # increase address to reach the next byte
        higher: int = self.read(self.pc)  # and read the higher part
        self.pc += 1  # increase again
        self.addr_abs = (higher << 8) | lower  # combine them
        return 0

    def ABX(self) -> int:
        """Addressing mode.
        Absolute addressing with X added to the address that
        is contained in the second and third byte."""
        lower: int = self.read(self.pc)
        self.pc += 1
        higher: int = self.read(self.pc)
        self.pc += 1

        _addr_abs: int = (higher << 8) | lower  # form the base address
        _addr_abs += self.x  # offset it by content in x register
        self.addr_abs = _addr_abs  # this may cause overflow (dealt below)

        # check if after addition an overflow is caused, the higher byte of
        # resultant address should be different from the original higher part.
        # if this occurs, we request one additional cycle to mimic the processor
        # dealing with carry flag.
        if _addr_abs & 0xFF00 != (higher << 8):
            return 1
        return 0

    def ABY(self) -> int:
        """Addressing mode.
        Absolute addressing with Y added to the address that
        is contained in the second and third byte."""
        lower: int = self.read(self.pc)
        self.pc += 1
        higher: int = self.read(self.pc)
        self.pc += 1

        _addr_abs: int = (higher << 8) | lower  # form the base address
        _addr_abs += self.y  # offset it by content in y register
        self.addr_abs = _addr_abs  # this may cause overflow (dealt below)

        if _addr_abs & 0xFF00 != (higher << 8):
            return 1
        return 0

    def IND(self) -> int:
        """Addressing mode."""

    def IZX(self) -> int:
        """Addressing mode."""

    def IZY(self) -> int:
        """Addressing mode."""

    # Opcode section (totally 56)
    def ADC(self) -> int:
        """Opcode function."""

    def AND(self) -> int:
        """Opcode function."""

    def ASL(self) -> int:
        """Opcode function."""

    def BCC(self) -> int:
        """Opcode function."""

    def BCS(self) -> int:
        """Opcode function."""

    def BEQ(self) -> int:
        """Opcode function."""

    def BIT(self) -> int:
        """Opcode function."""

    def BMI(self) -> int:
        """Opcode function."""

    def BNE(self) -> int:
        """Opcode function."""

    def BPL(self) -> int:
        """Opcode function."""

    def BRK(self) -> int:
        """Opcode function."""

    def BVC(self) -> int:
        """Opcode function."""

    def BVS(self) -> int:
        """Opcode function."""

    def CLC(self) -> int:
        """Opcode function."""

    def CLD(self) -> int:
        """Opcode function."""

    def CLI(self) -> int:
        """Opcode function."""

    def CLV(self) -> int:
        """Opcode function."""

    def CMP(self) -> int:
        """Opcode function."""

    def CPX(self) -> int:
        """Opcode function."""

    def CPY(self) -> int:
        """Opcode function."""

    def DEC(self) -> int:
        """Opcode function."""

    def DEX(self) -> int:
        """Opcode function."""

    def DEY(self) -> int:
        """Opcode function."""

    def EOR(self) -> int:
        """Opcode function."""

    def INC(self) -> int:
        """Opcode function."""

    def INX(self) -> int:
        """Opcode function."""

    def INY(self) -> int:
        """Opcode function."""

    def JMP(self) -> int:
        """Opcode function."""

    def JSR(self) -> int:
        """Opcode function."""

    def LDA(self) -> int:
        """Opcode function."""

    def LDX(self) -> int:
        """Opcode function."""

    def LDY(self) -> int:
        """Opcode function."""

    def LSR(self) -> int:
        """Opcode function."""

    def NOP(self) -> int:
        """Opcode function."""

    def ORA(self) -> int:
        """Opcode function."""

    def PHA(self) -> int:
        """Opcode function."""

    def PHP(self) -> int:
        """Opcode function."""

    def PLA(self) -> int:
        """Opcode function."""

    def PLP(self) -> int:
        """Opcode function."""

    def ROL(self) -> int:
        """Opcode function."""

    def ROR(self) -> int:
        """Opcode function."""

    def RTI(self) -> int:
        """Opcode function."""

    def RTS(self) -> int:
        """Opcode function."""

    def SBC(self) -> int:
        """Opcode function."""

    def SEC(self) -> int:
        """Opcode function."""

    def SED(self) -> int:
        """Opcode function."""

    def SEI(self) -> int:
        """Opcode function."""

    def STA(self) -> int:
        """Opcode function."""

    def STX(self) -> int:
        """Opcode function."""

    def STY(self) -> int:
        """Opcode function."""

    def TAX(self) -> int:
        """Opcode function."""

    def TAY(self) -> int:
        """Opcode function."""

    def TSX(self) -> int:
        """Opcode function."""

    def TXA(self) -> int:
        """Opcode function."""

    def TXS(self) -> int:
        """Opcode function."""

    def TYA(self) -> int:
        """Opcode function."""

    def XXX() -> int:
        """Special illegal opcode catcher."""

    def create_instructions(self) -> List[Instruction]:
        instructions: List[self.Instruction] = [
            self.Instruction(**instruction)
            for instruction in [
                {"name": "BRK", "opcode": self.BRK, "addrmode": self.IMM, "cycle": 7},
                {"name": "ORA", "opcode": self.ORA, "addrmode": self.IZX, "cycle": 6},
                {"name": "???", "opcode": self.XXX, "addrmode": self.IMP, "cycle": 2},
                {"name": "???", "opcode": self.XXX, "addrmode": self.IMP, "cycle": 8},
                {"name": "???", "opcode": self.NOP, "addrmode": self.IMP, "cycle": 3},
                {"name": "ORA", "opcode": self.ORA, "addrmode": self.ZP0, "cycle": 3},
                {"name": "ASL", "opcode": self.ASL, "addrmode": self.ZP0, "cycle": 5},
                {"name": "???", "opcode": self.XXX, "addrmode": self.IMP, "cycle": 5},
                {"name": "PHP", "opcode": self.PHP, "addrmode": self.IMP, "cycle": 3},
                {"name": "ORA", "opcode": self.ORA, "addrmode": self.IMM, "cycle": 2},
                {"name": "ASL", "opcode": self.ASL, "addrmode": self.IMP, "cycle": 2},
                {"name": "???", "opcode": self.XXX, "addrmode": self.IMP, "cycle": 2},
                {"name": "???", "opcode": self.NOP, "addrmode": self.IMP, "cycle": 4},
                {"name": "ORA", "opcode": self.ORA, "addrmode": self.ABS, "cycle": 4},
                {"name": "ASL", "opcode": self.ASL, "addrmode": self.ABS, "cycle": 6},
                {"name": "???", "opcode": self.XXX, "addrmode": self.IMP, "cycle": 6},
                {"name": "BPL", "opcode": self.BPL, "addrmode": self.REL, "cycle": 2},
                {"name": "ORA", "opcode": self.ORA, "addrmode": self.IZY, "cycle": 5},
                {"name": "???", "opcode": self.XXX, "addrmode": self.IMP, "cycle": 2},
                {"name": "???", "opcode": self.XXX, "addrmode": self.IMP, "cycle": 8},
                {"name": "???", "opcode": self.NOP, "addrmode": self.IMP, "cycle": 4},
                {"name": "ORA", "opcode": self.ORA, "addrmode": self.ZPX, "cycle": 4},
                {"name": "ASL", "opcode": self.ASL, "addrmode": self.ZPX, "cycle": 6},
                {"name": "???", "opcode": self.XXX, "addrmode": self.IMP, "cycle": 6},
                {"name": "CLC", "opcode": self.CLC, "addrmode": self.IMP, "cycle": 2},
                {"name": "ORA", "opcode": self.ORA, "addrmode": self.ABY, "cycle": 4},
                {"name": "???", "opcode": self.NOP, "addrmode": self.IMP, "cycle": 2},
                {"name": "???", "opcode": self.XXX, "addrmode": self.IMP, "cycle": 7},
                {"name": "???", "opcode": self.NOP, "addrmode": self.IMP, "cycle": 4},
                {"name": "ORA", "opcode": self.ORA, "addrmode": self.ABX, "cycle": 4},
                {"name": "ASL", "opcode": self.ASL, "addrmode": self.ABX, "cycle": 7},
                {"name": "???", "opcode": self.XXX, "addrmode": self.IMP, "cycle": 7},
                {"name": "JSR", "opcode": self.JSR, "addrmode": self.ABS, "cycle": 6},
                {"name": "AND", "opcode": self.AND, "addrmode": self.IZX, "cycle": 6},
                {"name": "???", "opcode": self.XXX, "addrmode": self.IMP, "cycle": 2},
                {"name": "???", "opcode": self.XXX, "addrmode": self.IMP, "cycle": 8},
                {"name": "BIT", "opcode": self.BIT, "addrmode": self.ZP0, "cycle": 3},
                {"name": "AND", "opcode": self.AND, "addrmode": self.ZP0, "cycle": 3},
                {"name": "ROL", "opcode": self.ROL, "addrmode": self.ZP0, "cycle": 5},
                {"name": "???", "opcode": self.XXX, "addrmode": self.IMP, "cycle": 5},
                {"name": "PLP", "opcode": self.PLP, "addrmode": self.IMP, "cycle": 4},
                {"name": "AND", "opcode": self.AND, "addrmode": self.IMM, "cycle": 2},
                {"name": "ROL", "opcode": self.ROL, "addrmode": self.IMP, "cycle": 2},
                {"name": "???", "opcode": self.XXX, "addrmode": self.IMP, "cycle": 2},
                {"name": "BIT", "opcode": self.BIT, "addrmode": self.ABS, "cycle": 4},
                {"name": "AND", "opcode": self.AND, "addrmode": self.ABS, "cycle": 4},
                {"name": "ROL", "opcode": self.ROL, "addrmode": self.ABS, "cycle": 6},
                {"name": "???", "opcode": self.XXX, "addrmode": self.IMP, "cycle": 6},
                {"name": "BMI", "opcode": self.BMI, "addrmode": self.REL, "cycle": 2},
                {"name": "AND", "opcode": self.AND, "addrmode": self.IZY, "cycle": 5},
                {"name": "???", "opcode": self.XXX, "addrmode": self.IMP, "cycle": 2},
                {"name": "???", "opcode": self.XXX, "addrmode": self.IMP, "cycle": 8},
                {"name": "???", "opcode": self.NOP, "addrmode": self.IMP, "cycle": 4},
                {"name": "AND", "opcode": self.AND, "addrmode": self.ZPX, "cycle": 4},
                {"name": "ROL", "opcode": self.ROL, "addrmode": self.ZPX, "cycle": 6},
                {"name": "???", "opcode": self.XXX, "addrmode": self.IMP, "cycle": 6},
                {"name": "SEC", "opcode": self.SEC, "addrmode": self.IMP, "cycle": 2},
                {"name": "AND", "opcode": self.AND, "addrmode": self.ABY, "cycle": 4},
                {"name": "???", "opcode": self.NOP, "addrmode": self.IMP, "cycle": 2},
                {"name": "???", "opcode": self.XXX, "addrmode": self.IMP, "cycle": 7},
                {"name": "???", "opcode": self.NOP, "addrmode": self.IMP, "cycle": 4},
                {"name": "AND", "opcode": self.AND, "addrmode": self.ABX, "cycle": 4},
                {"name": "ROL", "opcode": self.ROL, "addrmode": self.ABX, "cycle": 7},
                {"name": "???", "opcode": self.XXX, "addrmode": self.IMP, "cycle": 7},
                {"name": "RTI", "opcode": self.RTI, "addrmode": self.IMP, "cycle": 6},
                {"name": "EOR", "opcode": self.EOR, "addrmode": self.IZX, "cycle": 6},
                {"name": "???", "opcode": self.XXX, "addrmode": self.IMP, "cycle": 2},
                {"name": "???", "opcode": self.XXX, "addrmode": self.IMP, "cycle": 8},
                {"name": "???", "opcode": self.NOP, "addrmode": self.IMP, "cycle": 3},
                {"name": "EOR", "opcode": self.EOR, "addrmode": self.ZP0, "cycle": 3},
                {"name": "LSR", "opcode": self.LSR, "addrmode": self.ZP0, "cycle": 5},
                {"name": "???", "opcode": self.XXX, "addrmode": self.IMP, "cycle": 5},
                {"name": "PHA", "opcode": self.PHA, "addrmode": self.IMP, "cycle": 3},
                {"name": "EOR", "opcode": self.EOR, "addrmode": self.IMM, "cycle": 2},
                {"name": "LSR", "opcode": self.LSR, "addrmode": self.IMP, "cycle": 2},
                {"name": "???", "opcode": self.XXX, "addrmode": self.IMP, "cycle": 2},
                {"name": "JMP", "opcode": self.JMP, "addrmode": self.ABS, "cycle": 3},
                {"name": "EOR", "opcode": self.EOR, "addrmode": self.ABS, "cycle": 4},
                {"name": "LSR", "opcode": self.LSR, "addrmode": self.ABS, "cycle": 6},
                {"name": "???", "opcode": self.XXX, "addrmode": self.IMP, "cycle": 6},
                {"name": "BVC", "opcode": self.BVC, "addrmode": self.REL, "cycle": 2},
                {"name": "EOR", "opcode": self.EOR, "addrmode": self.IZY, "cycle": 5},
                {"name": "???", "opcode": self.XXX, "addrmode": self.IMP, "cycle": 2},
                {"name": "???", "opcode": self.XXX, "addrmode": self.IMP, "cycle": 8},
                {"name": "???", "opcode": self.NOP, "addrmode": self.IMP, "cycle": 4},
                {"name": "EOR", "opcode": self.EOR, "addrmode": self.ZPX, "cycle": 4},
                {"name": "LSR", "opcode": self.LSR, "addrmode": self.ZPX, "cycle": 6},
                {"name": "???", "opcode": self.XXX, "addrmode": self.IMP, "cycle": 6},
                {"name": "CLI", "opcode": self.CLI, "addrmode": self.IMP, "cycle": 2},
                {"name": "EOR", "opcode": self.EOR, "addrmode": self.ABY, "cycle": 4},
                {"name": "???", "opcode": self.NOP, "addrmode": self.IMP, "cycle": 2},
                {"name": "???", "opcode": self.XXX, "addrmode": self.IMP, "cycle": 7},
                {"name": "???", "opcode": self.NOP, "addrmode": self.IMP, "cycle": 4},
                {"name": "EOR", "opcode": self.EOR, "addrmode": self.ABX, "cycle": 4},
                {"name": "LSR", "opcode": self.LSR, "addrmode": self.ABX, "cycle": 7},
                {"name": "???", "opcode": self.XXX, "addrmode": self.IMP, "cycle": 7},
                {"name": "RTS", "opcode": self.RTS, "addrmode": self.IMP, "cycle": 6},
                {"name": "ADC", "opcode": self.ADC, "addrmode": self.IZX, "cycle": 6},
                {"name": "???", "opcode": self.XXX, "addrmode": self.IMP, "cycle": 2},
                {"name": "???", "opcode": self.XXX, "addrmode": self.IMP, "cycle": 8},
                {"name": "???", "opcode": self.NOP, "addrmode": self.IMP, "cycle": 3},
                {"name": "ADC", "opcode": self.ADC, "addrmode": self.ZP0, "cycle": 3},
                {"name": "ROR", "opcode": self.ROR, "addrmode": self.ZP0, "cycle": 5},
                {"name": "???", "opcode": self.XXX, "addrmode": self.IMP, "cycle": 5},
                {"name": "PLA", "opcode": self.PLA, "addrmode": self.IMP, "cycle": 4},
                {"name": "ADC", "opcode": self.ADC, "addrmode": self.IMM, "cycle": 2},
                {"name": "ROR", "opcode": self.ROR, "addrmode": self.IMP, "cycle": 2},
                {"name": "???", "opcode": self.XXX, "addrmode": self.IMP, "cycle": 2},
                {"name": "JMP", "opcode": self.JMP, "addrmode": self.IND, "cycle": 5},
                {"name": "ADC", "opcode": self.ADC, "addrmode": self.ABS, "cycle": 4},
                {"name": "ROR", "opcode": self.ROR, "addrmode": self.ABS, "cycle": 6},
                {"name": "???", "opcode": self.XXX, "addrmode": self.IMP, "cycle": 6},
                {"name": "BVS", "opcode": self.BVS, "addrmode": self.REL, "cycle": 2},
                {"name": "ADC", "opcode": self.ADC, "addrmode": self.IZY, "cycle": 5},
                {"name": "???", "opcode": self.XXX, "addrmode": self.IMP, "cycle": 2},
                {"name": "???", "opcode": self.XXX, "addrmode": self.IMP, "cycle": 8},
                {"name": "???", "opcode": self.NOP, "addrmode": self.IMP, "cycle": 4},
                {"name": "ADC", "opcode": self.ADC, "addrmode": self.ZPX, "cycle": 4},
                {"name": "ROR", "opcode": self.ROR, "addrmode": self.ZPX, "cycle": 6},
                {"name": "???", "opcode": self.XXX, "addrmode": self.IMP, "cycle": 6},
                {"name": "SEI", "opcode": self.SEI, "addrmode": self.IMP, "cycle": 2},
                {"name": "ADC", "opcode": self.ADC, "addrmode": self.ABY, "cycle": 4},
                {"name": "???", "opcode": self.NOP, "addrmode": self.IMP, "cycle": 2},
                {"name": "???", "opcode": self.XXX, "addrmode": self.IMP, "cycle": 7},
                {"name": "???", "opcode": self.NOP, "addrmode": self.IMP, "cycle": 4},
                {"name": "ADC", "opcode": self.ADC, "addrmode": self.ABX, "cycle": 4},
                {"name": "ROR", "opcode": self.ROR, "addrmode": self.ABX, "cycle": 7},
                {"name": "???", "opcode": self.XXX, "addrmode": self.IMP, "cycle": 7},
                {"name": "???", "opcode": self.NOP, "addrmode": self.IMP, "cycle": 2},
                {"name": "STA", "opcode": self.STA, "addrmode": self.IZX, "cycle": 6},
                {"name": "???", "opcode": self.NOP, "addrmode": self.IMP, "cycle": 2},
                {"name": "???", "opcode": self.XXX, "addrmode": self.IMP, "cycle": 6},
                {"name": "STY", "opcode": self.STY, "addrmode": self.ZP0, "cycle": 3},
                {"name": "STA", "opcode": self.STA, "addrmode": self.ZP0, "cycle": 3},
                {"name": "STX", "opcode": self.STX, "addrmode": self.ZP0, "cycle": 3},
                {"name": "???", "opcode": self.XXX, "addrmode": self.IMP, "cycle": 3},
                {"name": "DEY", "opcode": self.DEY, "addrmode": self.IMP, "cycle": 2},
                {"name": "???", "opcode": self.NOP, "addrmode": self.IMP, "cycle": 2},
                {"name": "TXA", "opcode": self.TXA, "addrmode": self.IMP, "cycle": 2},
                {"name": "???", "opcode": self.XXX, "addrmode": self.IMP, "cycle": 2},
                {"name": "STY", "opcode": self.STY, "addrmode": self.ABS, "cycle": 4},
                {"name": "STA", "opcode": self.STA, "addrmode": self.ABS, "cycle": 4},
                {"name": "STX", "opcode": self.STX, "addrmode": self.ABS, "cycle": 4},
                {"name": "???", "opcode": self.XXX, "addrmode": self.IMP, "cycle": 4},
                {"name": "BCC", "opcode": self.BCC, "addrmode": self.REL, "cycle": 2},
                {"name": "STA", "opcode": self.STA, "addrmode": self.IZY, "cycle": 6},
                {"name": "???", "opcode": self.XXX, "addrmode": self.IMP, "cycle": 2},
                {"name": "???", "opcode": self.XXX, "addrmode": self.IMP, "cycle": 6},
                {"name": "STY", "opcode": self.STY, "addrmode": self.ZPX, "cycle": 4},
                {"name": "STA", "opcode": self.STA, "addrmode": self.ZPX, "cycle": 4},
                {"name": "STX", "opcode": self.STX, "addrmode": self.ZPY, "cycle": 4},
                {"name": "???", "opcode": self.XXX, "addrmode": self.IMP, "cycle": 4},
                {"name": "TYA", "opcode": self.TYA, "addrmode": self.IMP, "cycle": 2},
                {"name": "STA", "opcode": self.STA, "addrmode": self.ABY, "cycle": 5},
                {"name": "TXS", "opcode": self.TXS, "addrmode": self.IMP, "cycle": 2},
                {"name": "???", "opcode": self.XXX, "addrmode": self.IMP, "cycle": 5},
                {"name": "???", "opcode": self.NOP, "addrmode": self.IMP, "cycle": 5},
                {"name": "STA", "opcode": self.STA, "addrmode": self.ABX, "cycle": 5},
                {"name": "???", "opcode": self.XXX, "addrmode": self.IMP, "cycle": 5},
                {"name": "???", "opcode": self.XXX, "addrmode": self.IMP, "cycle": 5},
                {"name": "LDY", "opcode": self.LDY, "addrmode": self.IMM, "cycle": 2},
                {"name": "LDA", "opcode": self.LDA, "addrmode": self.IZX, "cycle": 6},
                {"name": "LDX", "opcode": self.LDX, "addrmode": self.IMM, "cycle": 2},
                {"name": "???", "opcode": self.XXX, "addrmode": self.IMP, "cycle": 6},
                {"name": "LDY", "opcode": self.LDY, "addrmode": self.ZP0, "cycle": 3},
                {"name": "LDA", "opcode": self.LDA, "addrmode": self.ZP0, "cycle": 3},
                {"name": "LDX", "opcode": self.LDX, "addrmode": self.ZP0, "cycle": 3},
                {"name": "???", "opcode": self.XXX, "addrmode": self.IMP, "cycle": 3},
                {"name": "TAY", "opcode": self.TAY, "addrmode": self.IMP, "cycle": 2},
                {"name": "LDA", "opcode": self.LDA, "addrmode": self.IMM, "cycle": 2},
                {"name": "TAX", "opcode": self.TAX, "addrmode": self.IMP, "cycle": 2},
                {"name": "???", "opcode": self.XXX, "addrmode": self.IMP, "cycle": 2},
                {"name": "LDY", "opcode": self.LDY, "addrmode": self.ABS, "cycle": 4},
                {"name": "LDA", "opcode": self.LDA, "addrmode": self.ABS, "cycle": 4},
                {"name": "LDX", "opcode": self.LDX, "addrmode": self.ABS, "cycle": 4},
                {"name": "???", "opcode": self.XXX, "addrmode": self.IMP, "cycle": 4},
                {"name": "BCS", "opcode": self.BCS, "addrmode": self.REL, "cycle": 2},
                {"name": "LDA", "opcode": self.LDA, "addrmode": self.IZY, "cycle": 5},
                {"name": "???", "opcode": self.XXX, "addrmode": self.IMP, "cycle": 2},
                {"name": "???", "opcode": self.XXX, "addrmode": self.IMP, "cycle": 5},
                {"name": "LDY", "opcode": self.LDY, "addrmode": self.ZPX, "cycle": 4},
                {"name": "LDA", "opcode": self.LDA, "addrmode": self.ZPX, "cycle": 4},
                {"name": "LDX", "opcode": self.LDX, "addrmode": self.ZPY, "cycle": 4},
                {"name": "???", "opcode": self.XXX, "addrmode": self.IMP, "cycle": 4},
                {"name": "CLV", "opcode": self.CLV, "addrmode": self.IMP, "cycle": 2},
                {"name": "LDA", "opcode": self.LDA, "addrmode": self.ABY, "cycle": 4},
                {"name": "TSX", "opcode": self.TSX, "addrmode": self.IMP, "cycle": 2},
                {"name": "???", "opcode": self.XXX, "addrmode": self.IMP, "cycle": 4},
                {"name": "LDY", "opcode": self.LDY, "addrmode": self.ABX, "cycle": 4},
                {"name": "LDA", "opcode": self.LDA, "addrmode": self.ABX, "cycle": 4},
                {"name": "LDX", "opcode": self.LDX, "addrmode": self.ABY, "cycle": 4},
                {"name": "???", "opcode": self.XXX, "addrmode": self.IMP, "cycle": 4},
                {"name": "CPY", "opcode": self.CPY, "addrmode": self.IMM, "cycle": 2},
                {"name": "CMP", "opcode": self.CMP, "addrmode": self.IZX, "cycle": 6},
                {"name": "???", "opcode": self.NOP, "addrmode": self.IMP, "cycle": 2},
                {"name": "???", "opcode": self.XXX, "addrmode": self.IMP, "cycle": 8},
                {"name": "CPY", "opcode": self.CPY, "addrmode": self.ZP0, "cycle": 3},
                {"name": "CMP", "opcode": self.CMP, "addrmode": self.ZP0, "cycle": 3},
                {"name": "DEC", "opcode": self.DEC, "addrmode": self.ZP0, "cycle": 5},
                {"name": "???", "opcode": self.XXX, "addrmode": self.IMP, "cycle": 5},
                {"name": "INY", "opcode": self.INY, "addrmode": self.IMP, "cycle": 2},
                {"name": "CMP", "opcode": self.CMP, "addrmode": self.IMM, "cycle": 2},
                {"name": "DEX", "opcode": self.DEX, "addrmode": self.IMP, "cycle": 2},
                {"name": "???", "opcode": self.XXX, "addrmode": self.IMP, "cycle": 2},
                {"name": "CPY", "opcode": self.CPY, "addrmode": self.ABS, "cycle": 4},
                {"name": "CMP", "opcode": self.CMP, "addrmode": self.ABS, "cycle": 4},
                {"name": "DEC", "opcode": self.DEC, "addrmode": self.ABS, "cycle": 6},
                {"name": "???", "opcode": self.XXX, "addrmode": self.IMP, "cycle": 6},
                {"name": "BNE", "opcode": self.BNE, "addrmode": self.REL, "cycle": 2},
                {"name": "CMP", "opcode": self.CMP, "addrmode": self.IZY, "cycle": 5},
                {"name": "???", "opcode": self.XXX, "addrmode": self.IMP, "cycle": 2},
                {"name": "???", "opcode": self.XXX, "addrmode": self.IMP, "cycle": 8},
                {"name": "???", "opcode": self.NOP, "addrmode": self.IMP, "cycle": 4},
                {"name": "CMP", "opcode": self.CMP, "addrmode": self.ZPX, "cycle": 4},
                {"name": "DEC", "opcode": self.DEC, "addrmode": self.ZPX, "cycle": 6},
                {"name": "???", "opcode": self.XXX, "addrmode": self.IMP, "cycle": 6},
                {"name": "CLD", "opcode": self.CLD, "addrmode": self.IMP, "cycle": 2},
                {"name": "CMP", "opcode": self.CMP, "addrmode": self.ABY, "cycle": 4},
                {"name": "NOP", "opcode": self.NOP, "addrmode": self.IMP, "cycle": 2},
                {"name": "???", "opcode": self.XXX, "addrmode": self.IMP, "cycle": 7},
                {"name": "???", "opcode": self.NOP, "addrmode": self.IMP, "cycle": 4},
                {"name": "CMP", "opcode": self.CMP, "addrmode": self.ABX, "cycle": 4},
                {"name": "DEC", "opcode": self.DEC, "addrmode": self.ABX, "cycle": 7},
                {"name": "???", "opcode": self.XXX, "addrmode": self.IMP, "cycle": 7},
                {"name": "CPX", "opcode": self.CPX, "addrmode": self.IMM, "cycle": 2},
                {"name": "SBC", "opcode": self.SBC, "addrmode": self.IZX, "cycle": 6},
                {"name": "???", "opcode": self.NOP, "addrmode": self.IMP, "cycle": 2},
                {"name": "???", "opcode": self.XXX, "addrmode": self.IMP, "cycle": 8},
                {"name": "CPX", "opcode": self.CPX, "addrmode": self.ZP0, "cycle": 3},
                {"name": "SBC", "opcode": self.SBC, "addrmode": self.ZP0, "cycle": 3},
                {"name": "INC", "opcode": self.INC, "addrmode": self.ZP0, "cycle": 5},
                {"name": "???", "opcode": self.XXX, "addrmode": self.IMP, "cycle": 5},
                {"name": "INX", "opcode": self.INX, "addrmode": self.IMP, "cycle": 2},
                {"name": "SBC", "opcode": self.SBC, "addrmode": self.IMM, "cycle": 2},
                {"name": "NOP", "opcode": self.NOP, "addrmode": self.IMP, "cycle": 2},
                {"name": "???", "opcode": self.SBC, "addrmode": self.IMP, "cycle": 2},
                {"name": "CPX", "opcode": self.CPX, "addrmode": self.ABS, "cycle": 4},
                {"name": "SBC", "opcode": self.SBC, "addrmode": self.ABS, "cycle": 4},
                {"name": "INC", "opcode": self.INC, "addrmode": self.ABS, "cycle": 6},
                {"name": "???", "opcode": self.XXX, "addrmode": self.IMP, "cycle": 6},
                {"name": "BEQ", "opcode": self.BEQ, "addrmode": self.REL, "cycle": 2},
                {"name": "SBC", "opcode": self.SBC, "addrmode": self.IZY, "cycle": 5},
                {"name": "???", "opcode": self.XXX, "addrmode": self.IMP, "cycle": 2},
                {"name": "???", "opcode": self.XXX, "addrmode": self.IMP, "cycle": 8},
                {"name": "???", "opcode": self.NOP, "addrmode": self.IMP, "cycle": 4},
                {"name": "SBC", "opcode": self.SBC, "addrmode": self.ZPX, "cycle": 4},
                {"name": "INC", "opcode": self.INC, "addrmode": self.ZPX, "cycle": 6},
                {"name": "???", "opcode": self.XXX, "addrmode": self.IMP, "cycle": 6},
                {"name": "SED", "opcode": self.SED, "addrmode": self.IMP, "cycle": 2},
                {"name": "SBC", "opcode": self.SBC, "addrmode": self.ABY, "cycle": 4},
                {"name": "NOP", "opcode": self.NOP, "addrmode": self.IMP, "cycle": 2},
                {"name": "???", "opcode": self.XXX, "addrmode": self.IMP, "cycle": 7},
                {"name": "???", "opcode": self.NOP, "addrmode": self.IMP, "cycle": 4},
                {"name": "SBC", "opcode": self.SBC, "addrmode": self.ABX, "cycle": 4},
                {"name": "INC", "opcode": self.INC, "addrmode": self.ABX, "cycle": 7},
                {"name": "???", "opcode": self.XXX, "addrmode": self.IMP, "cycle": 7},
            ]
        ]

        return instructions
