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
        self.pc: int = 0x00  # program counter
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
            add_cycle += (add_cycle_address & add_cycle_operation)
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
    def IMP() -> int:
        """Addressing mode."""

    def IMM() -> int:
        """Addressing mode."""

    def ZP0() -> int:
        """Addressing mode."""

    def ZPX() -> int:
        """Addressing mode."""

    def ZPY() -> int:
        """Addressing mode."""

    def REL() -> int:
        """Addressing mode."""

    def ABS() -> int:
        """Addressing mode."""

    def ABX() -> int:
        """Addressing mode."""

    def ABY() -> int:
        """Addressing mode."""

    def IND() -> int:
        """Addressing mode."""

    def IZX() -> int:
        """Addressing mode."""

    def IZY() -> int:
        """Addressing mode."""

    # Opcode section (totally 56)
    def ADC() -> int:
        """Opcodes."""

    def AND() -> int:
        """Opcodes."""

    def ASL() -> int:
        """Opcodes."""

    def BCC() -> int:
        """Opcodes."""

    def BCS() -> int:
        """Opcodes."""

    def BEQ() -> int:
        """Opcodes."""

    def BIT() -> int:
        """Opcodes."""

    def BMI() -> int:
        """Opcodes."""

    def BNE() -> int:
        """Opcodes."""

    def BPL() -> int:
        """Opcodes."""

    def BRK() -> int:
        """Opcodes."""

    def BVC() -> int:
        """Opcodes."""

    def BVS() -> int:
        """Opcodes."""

    def CLC() -> int:
        """Opcodes."""

    def CLD() -> int:
        """Opcodes."""

    def CLI() -> int:
        """Opcodes."""

    def CLV() -> int:
        """Opcodes."""

    def CMP() -> int:
        """Opcodes."""

    def CPX() -> int:
        """Opcodes."""

    def CPY() -> int:
        """Opcodes."""

    def DEC() -> int:
        """Opcodes."""

    def DEX() -> int:
        """Opcodes."""

    def DEY() -> int:
        """Opcodes."""

    def EOR() -> int:
        """Opcodes."""

    def INC() -> int:
        """Opcodes."""

    def INX() -> int:
        """Opcodes."""

    def INY() -> int:
        """Opcodes."""

    def JMP() -> int:
        """Opcodes."""

    def JSR() -> int:
        """Opcodes."""

    def LDA() -> int:
        """Opcodes."""

    def LDX() -> int:
        """Opcodes."""

    def LDY() -> int:
        """Opcodes."""

    def LSR() -> int:
        """Opcodes."""

    def NOP() -> int:
        """Opcodes."""

    def ORA() -> int:
        """Opcodes."""

    def PHA() -> int:
        """Opcodes."""

    def PHP() -> int:
        """Opcodes."""

    def PLA() -> int:
        """Opcodes."""

    def PLP() -> int:
        """Opcodes."""

    def ROL() -> int:
        """Opcodes."""

    def ROR() -> int:
        """Opcodes."""

    def RTI() -> int:
        """Opcodes."""

    def RTS() -> int:
        """Opcodes."""

    def SBC() -> int:
        """Opcodes."""

    def SEC() -> int:
        """Opcodes."""

    def SED() -> int:
        """Opcodes."""

    def SEI() -> int:
        """Opcodes."""

    def STA() -> int:
        """Opcodes."""

    def STX() -> int:
        """Opcodes."""

    def STY() -> int:
        """Opcodes."""

    def TAX() -> int:
        """Opcodes."""

    def TAY() -> int:
        """Opcodes."""

    def TSX() -> int:
        """Opcodes."""

    def TXA() -> int:
        """Opcodes."""

    def TXS() -> int:
        """Opcodes."""

    def TYA() -> int:
        """Opcodes."""

    def XXX() -> int:
        """Special illegal opcode catcher."""

    def create_instructions(self) -> List[Instruction]:
        instructions: Dict[str, self.Instruction] = {
            opcode: self.Instruction(**instruction)
            for opcode, instruction in [
                ("BRK", {"opcode": self.BRK, "addrmode": self.IMM, "cycle": 7}),
                ("ORA", {"opcode": self.ORA, "addrmode": self.IZX, "cycle": 6}),
                ("???", {"opcode": self.XXX, "addrmode": self.IMP, "cycle": 2}),
                ("???", {"opcode": self.XXX, "addrmode": self.IMP, "cycle": 8}),
                ("???", {"opcode": self.NOP, "addrmode": self.IMP, "cycle": 3}),
                ("ORA", {"opcode": self.ORA, "addrmode": self.ZP0, "cycle": 3}),
                ("ASL", {"opcode": self.ASL, "addrmode": self.ZP0, "cycle": 5}),
                ("???", {"opcode": self.XXX, "addrmode": self.IMP, "cycle": 5}),
                ("PHP", {"opcode": self.PHP, "addrmode": self.IMP, "cycle": 3}),
                ("ORA", {"opcode": self.ORA, "addrmode": self.IMM, "cycle": 2}),
                ("ASL", {"opcode": self.ASL, "addrmode": self.IMP, "cycle": 2}),
                ("???", {"opcode": self.XXX, "addrmode": self.IMP, "cycle": 2}),
                ("???", {"opcode": self.NOP, "addrmode": self.IMP, "cycle": 4}),
                ("ORA", {"opcode": self.ORA, "addrmode": self.ABS, "cycle": 4}),
                ("ASL", {"opcode": self.ASL, "addrmode": self.ABS, "cycle": 6}),
                ("???", {"opcode": self.XXX, "addrmode": self.IMP, "cycle": 6}),
                ("BPL", {"opcode": self.BPL, "addrmode": self.REL, "cycle": 2}),
                ("ORA", {"opcode": self.ORA, "addrmode": self.IZY, "cycle": 5}),
                ("???", {"opcode": self.XXX, "addrmode": self.IMP, "cycle": 2}),
                ("???", {"opcode": self.XXX, "addrmode": self.IMP, "cycle": 8}),
                ("???", {"opcode": self.NOP, "addrmode": self.IMP, "cycle": 4}),
                ("ORA", {"opcode": self.ORA, "addrmode": self.ZPX, "cycle": 4}),
                ("ASL", {"opcode": self.ASL, "addrmode": self.ZPX, "cycle": 6}),
                ("???", {"opcode": self.XXX, "addrmode": self.IMP, "cycle": 6}),
                ("CLC", {"opcode": self.CLC, "addrmode": self.IMP, "cycle": 2}),
                ("ORA", {"opcode": self.ORA, "addrmode": self.ABY, "cycle": 4}),
                ("???", {"opcode": self.NOP, "addrmode": self.IMP, "cycle": 2}),
                ("???", {"opcode": self.XXX, "addrmode": self.IMP, "cycle": 7}),
                ("???", {"opcode": self.NOP, "addrmode": self.IMP, "cycle": 4}),
                ("ORA", {"opcode": self.ORA, "addrmode": self.ABX, "cycle": 4}),
                ("ASL", {"opcode": self.ASL, "addrmode": self.ABX, "cycle": 7}),
                ("???", {"opcode": self.XXX, "addrmode": self.IMP, "cycle": 7}),
                ("JSR", {"opcode": self.JSR, "addrmode": self.ABS, "cycle": 6}),
                ("AND", {"opcode": self.AND, "addrmode": self.IZX, "cycle": 6}),
                ("???", {"opcode": self.XXX, "addrmode": self.IMP, "cycle": 2}),
                ("???", {"opcode": self.XXX, "addrmode": self.IMP, "cycle": 8}),
                ("BIT", {"opcode": self.BIT, "addrmode": self.ZP0, "cycle": 3}),
                ("AND", {"opcode": self.AND, "addrmode": self.ZP0, "cycle": 3}),
                ("ROL", {"opcode": self.ROL, "addrmode": self.ZP0, "cycle": 5}),
                ("???", {"opcode": self.XXX, "addrmode": self.IMP, "cycle": 5}),
                ("PLP", {"opcode": self.PLP, "addrmode": self.IMP, "cycle": 4}),
                ("AND", {"opcode": self.AND, "addrmode": self.IMM, "cycle": 2}),
                ("ROL", {"opcode": self.ROL, "addrmode": self.IMP, "cycle": 2}),
                ("???", {"opcode": self.XXX, "addrmode": self.IMP, "cycle": 2}),
                ("BIT", {"opcode": self.BIT, "addrmode": self.ABS, "cycle": 4}),
                ("AND", {"opcode": self.AND, "addrmode": self.ABS, "cycle": 4}),
                ("ROL", {"opcode": self.ROL, "addrmode": self.ABS, "cycle": 6}),
                ("???", {"opcode": self.XXX, "addrmode": self.IMP, "cycle": 6}),
                ("BMI", {"opcode": self.BMI, "addrmode": self.REL, "cycle": 2}),
                ("AND", {"opcode": self.AND, "addrmode": self.IZY, "cycle": 5}),
                ("???", {"opcode": self.XXX, "addrmode": self.IMP, "cycle": 2}),
                ("???", {"opcode": self.XXX, "addrmode": self.IMP, "cycle": 8}),
                ("???", {"opcode": self.NOP, "addrmode": self.IMP, "cycle": 4}),
                ("AND", {"opcode": self.AND, "addrmode": self.ZPX, "cycle": 4}),
                ("ROL", {"opcode": self.ROL, "addrmode": self.ZPX, "cycle": 6}),
                ("???", {"opcode": self.XXX, "addrmode": self.IMP, "cycle": 6}),
                ("SEC", {"opcode": self.SEC, "addrmode": self.IMP, "cycle": 2}),
                ("AND", {"opcode": self.AND, "addrmode": self.ABY, "cycle": 4}),
                ("???", {"opcode": self.NOP, "addrmode": self.IMP, "cycle": 2}),
                ("???", {"opcode": self.XXX, "addrmode": self.IMP, "cycle": 7}),
                ("???", {"opcode": self.NOP, "addrmode": self.IMP, "cycle": 4}),
                ("AND", {"opcode": self.AND, "addrmode": self.ABX, "cycle": 4}),
                ("ROL", {"opcode": self.ROL, "addrmode": self.ABX, "cycle": 7}),
                ("???", {"opcode": self.XXX, "addrmode": self.IMP, "cycle": 7}),
                ("RTI", {"opcode": self.RTI, "addrmode": self.IMP, "cycle": 6}),
                ("EOR", {"opcode": self.EOR, "addrmode": self.IZX, "cycle": 6}),
                ("???", {"opcode": self.XXX, "addrmode": self.IMP, "cycle": 2}),
                ("???", {"opcode": self.XXX, "addrmode": self.IMP, "cycle": 8}),
                ("???", {"opcode": self.NOP, "addrmode": self.IMP, "cycle": 3}),
                ("EOR", {"opcode": self.EOR, "addrmode": self.ZP0, "cycle": 3}),
                ("LSR", {"opcode": self.LSR, "addrmode": self.ZP0, "cycle": 5}),
                ("???", {"opcode": self.XXX, "addrmode": self.IMP, "cycle": 5}),
                ("PHA", {"opcode": self.PHA, "addrmode": self.IMP, "cycle": 3}),
                ("EOR", {"opcode": self.EOR, "addrmode": self.IMM, "cycle": 2}),
                ("LSR", {"opcode": self.LSR, "addrmode": self.IMP, "cycle": 2}),
                ("???", {"opcode": self.XXX, "addrmode": self.IMP, "cycle": 2}),
                ("JMP", {"opcode": self.JMP, "addrmode": self.ABS, "cycle": 3}),
                ("EOR", {"opcode": self.EOR, "addrmode": self.ABS, "cycle": 4}),
                ("LSR", {"opcode": self.LSR, "addrmode": self.ABS, "cycle": 6}),
                ("???", {"opcode": self.XXX, "addrmode": self.IMP, "cycle": 6}),
                ("BVC", {"opcode": self.BVC, "addrmode": self.REL, "cycle": 2}),
                ("EOR", {"opcode": self.EOR, "addrmode": self.IZY, "cycle": 5}),
                ("???", {"opcode": self.XXX, "addrmode": self.IMP, "cycle": 2}),
                ("???", {"opcode": self.XXX, "addrmode": self.IMP, "cycle": 8}),
                ("???", {"opcode": self.NOP, "addrmode": self.IMP, "cycle": 4}),
                ("EOR", {"opcode": self.EOR, "addrmode": self.ZPX, "cycle": 4}),
                ("LSR", {"opcode": self.LSR, "addrmode": self.ZPX, "cycle": 6}),
                ("???", {"opcode": self.XXX, "addrmode": self.IMP, "cycle": 6}),
                ("CLI", {"opcode": self.CLI, "addrmode": self.IMP, "cycle": 2}),
                ("EOR", {"opcode": self.EOR, "addrmode": self.ABY, "cycle": 4}),
                ("???", {"opcode": self.NOP, "addrmode": self.IMP, "cycle": 2}),
                ("???", {"opcode": self.XXX, "addrmode": self.IMP, "cycle": 7}),
                ("???", {"opcode": self.NOP, "addrmode": self.IMP, "cycle": 4}),
                ("EOR", {"opcode": self.EOR, "addrmode": self.ABX, "cycle": 4}),
                ("LSR", {"opcode": self.LSR, "addrmode": self.ABX, "cycle": 7}),
                ("???", {"opcode": self.XXX, "addrmode": self.IMP, "cycle": 7}),
                ("RTS", {"opcode": self.RTS, "addrmode": self.IMP, "cycle": 6}),
                ("ADC", {"opcode": self.ADC, "addrmode": self.IZX, "cycle": 6}),
                ("???", {"opcode": self.XXX, "addrmode": self.IMP, "cycle": 2}),
                ("???", {"opcode": self.XXX, "addrmode": self.IMP, "cycle": 8}),
                ("???", {"opcode": self.NOP, "addrmode": self.IMP, "cycle": 3}),
                ("ADC", {"opcode": self.ADC, "addrmode": self.ZP0, "cycle": 3}),
                ("ROR", {"opcode": self.ROR, "addrmode": self.ZP0, "cycle": 5}),
                ("???", {"opcode": self.XXX, "addrmode": self.IMP, "cycle": 5}),
                ("PLA", {"opcode": self.PLA, "addrmode": self.IMP, "cycle": 4}),
                ("ADC", {"opcode": self.ADC, "addrmode": self.IMM, "cycle": 2}),
                ("ROR", {"opcode": self.ROR, "addrmode": self.IMP, "cycle": 2}),
                ("???", {"opcode": self.XXX, "addrmode": self.IMP, "cycle": 2}),
                ("JMP", {"opcode": self.JMP, "addrmode": self.IND, "cycle": 5}),
                ("ADC", {"opcode": self.ADC, "addrmode": self.ABS, "cycle": 4}),
                ("ROR", {"opcode": self.ROR, "addrmode": self.ABS, "cycle": 6}),
                ("???", {"opcode": self.XXX, "addrmode": self.IMP, "cycle": 6}),
                ("BVS", {"opcode": self.BVS, "addrmode": self.REL, "cycle": 2}),
                ("ADC", {"opcode": self.ADC, "addrmode": self.IZY, "cycle": 5}),
                ("???", {"opcode": self.XXX, "addrmode": self.IMP, "cycle": 2}),
                ("???", {"opcode": self.XXX, "addrmode": self.IMP, "cycle": 8}),
                ("???", {"opcode": self.NOP, "addrmode": self.IMP, "cycle": 4}),
                ("ADC", {"opcode": self.ADC, "addrmode": self.ZPX, "cycle": 4}),
                ("ROR", {"opcode": self.ROR, "addrmode": self.ZPX, "cycle": 6}),
                ("???", {"opcode": self.XXX, "addrmode": self.IMP, "cycle": 6}),
                ("SEI", {"opcode": self.SEI, "addrmode": self.IMP, "cycle": 2}),
                ("ADC", {"opcode": self.ADC, "addrmode": self.ABY, "cycle": 4}),
                ("???", {"opcode": self.NOP, "addrmode": self.IMP, "cycle": 2}),
                ("???", {"opcode": self.XXX, "addrmode": self.IMP, "cycle": 7}),
                ("???", {"opcode": self.NOP, "addrmode": self.IMP, "cycle": 4}),
                ("ADC", {"opcode": self.ADC, "addrmode": self.ABX, "cycle": 4}),
                ("ROR", {"opcode": self.ROR, "addrmode": self.ABX, "cycle": 7}),
                ("???", {"opcode": self.XXX, "addrmode": self.IMP, "cycle": 7}),
                ("???", {"opcode": self.NOP, "addrmode": self.IMP, "cycle": 2}),
                ("STA", {"opcode": self.STA, "addrmode": self.IZX, "cycle": 6}),
                ("???", {"opcode": self.NOP, "addrmode": self.IMP, "cycle": 2}),
                ("???", {"opcode": self.XXX, "addrmode": self.IMP, "cycle": 6}),
                ("STY", {"opcode": self.STY, "addrmode": self.ZP0, "cycle": 3}),
                ("STA", {"opcode": self.STA, "addrmode": self.ZP0, "cycle": 3}),
                ("STX", {"opcode": self.STX, "addrmode": self.ZP0, "cycle": 3}),
                ("???", {"opcode": self.XXX, "addrmode": self.IMP, "cycle": 3}),
                ("DEY", {"opcode": self.DEY, "addrmode": self.IMP, "cycle": 2}),
                ("???", {"opcode": self.NOP, "addrmode": self.IMP, "cycle": 2}),
                ("TXA", {"opcode": self.TXA, "addrmode": self.IMP, "cycle": 2}),
                ("???", {"opcode": self.XXX, "addrmode": self.IMP, "cycle": 2}),
                ("STY", {"opcode": self.STY, "addrmode": self.ABS, "cycle": 4}),
                ("STA", {"opcode": self.STA, "addrmode": self.ABS, "cycle": 4}),
                ("STX", {"opcode": self.STX, "addrmode": self.ABS, "cycle": 4}),
                ("???", {"opcode": self.XXX, "addrmode": self.IMP, "cycle": 4}),
                ("BCC", {"opcode": self.BCC, "addrmode": self.REL, "cycle": 2}),
                ("STA", {"opcode": self.STA, "addrmode": self.IZY, "cycle": 6}),
                ("???", {"opcode": self.XXX, "addrmode": self.IMP, "cycle": 2}),
                ("???", {"opcode": self.XXX, "addrmode": self.IMP, "cycle": 6}),
                ("STY", {"opcode": self.STY, "addrmode": self.ZPX, "cycle": 4}),
                ("STA", {"opcode": self.STA, "addrmode": self.ZPX, "cycle": 4}),
                ("STX", {"opcode": self.STX, "addrmode": self.ZPY, "cycle": 4}),
                ("???", {"opcode": self.XXX, "addrmode": self.IMP, "cycle": 4}),
                ("TYA", {"opcode": self.TYA, "addrmode": self.IMP, "cycle": 2}),
                ("STA", {"opcode": self.STA, "addrmode": self.ABY, "cycle": 5}),
                ("TXS", {"opcode": self.TXS, "addrmode": self.IMP, "cycle": 2}),
                ("???", {"opcode": self.XXX, "addrmode": self.IMP, "cycle": 5}),
                ("???", {"opcode": self.NOP, "addrmode": self.IMP, "cycle": 5}),
                ("STA", {"opcode": self.STA, "addrmode": self.ABX, "cycle": 5}),
                ("???", {"opcode": self.XXX, "addrmode": self.IMP, "cycle": 5}),
                ("???", {"opcode": self.XXX, "addrmode": self.IMP, "cycle": 5}),
                ("LDY", {"opcode": self.LDY, "addrmode": self.IMM, "cycle": 2}),
                ("LDA", {"opcode": self.LDA, "addrmode": self.IZX, "cycle": 6}),
                ("LDX", {"opcode": self.LDX, "addrmode": self.IMM, "cycle": 2}),
                ("???", {"opcode": self.XXX, "addrmode": self.IMP, "cycle": 6}),
                ("LDY", {"opcode": self.LDY, "addrmode": self.ZP0, "cycle": 3}),
                ("LDA", {"opcode": self.LDA, "addrmode": self.ZP0, "cycle": 3}),
                ("LDX", {"opcode": self.LDX, "addrmode": self.ZP0, "cycle": 3}),
                ("???", {"opcode": self.XXX, "addrmode": self.IMP, "cycle": 3}),
                ("TAY", {"opcode": self.TAY, "addrmode": self.IMP, "cycle": 2}),
                ("LDA", {"opcode": self.LDA, "addrmode": self.IMM, "cycle": 2}),
                ("TAX", {"opcode": self.TAX, "addrmode": self.IMP, "cycle": 2}),
                ("???", {"opcode": self.XXX, "addrmode": self.IMP, "cycle": 2}),
                ("LDY", {"opcode": self.LDY, "addrmode": self.ABS, "cycle": 4}),
                ("LDA", {"opcode": self.LDA, "addrmode": self.ABS, "cycle": 4}),
                ("LDX", {"opcode": self.LDX, "addrmode": self.ABS, "cycle": 4}),
                ("???", {"opcode": self.XXX, "addrmode": self.IMP, "cycle": 4}),
                ("BCS", {"opcode": self.BCS, "addrmode": self.REL, "cycle": 2}),
                ("LDA", {"opcode": self.LDA, "addrmode": self.IZY, "cycle": 5}),
                ("???", {"opcode": self.XXX, "addrmode": self.IMP, "cycle": 2}),
                ("???", {"opcode": self.XXX, "addrmode": self.IMP, "cycle": 5}),
                ("LDY", {"opcode": self.LDY, "addrmode": self.ZPX, "cycle": 4}),
                ("LDA", {"opcode": self.LDA, "addrmode": self.ZPX, "cycle": 4}),
                ("LDX", {"opcode": self.LDX, "addrmode": self.ZPY, "cycle": 4}),
                ("???", {"opcode": self.XXX, "addrmode": self.IMP, "cycle": 4}),
                ("CLV", {"opcode": self.CLV, "addrmode": self.IMP, "cycle": 2}),
                ("LDA", {"opcode": self.LDA, "addrmode": self.ABY, "cycle": 4}),
                ("TSX", {"opcode": self.TSX, "addrmode": self.IMP, "cycle": 2}),
                ("???", {"opcode": self.XXX, "addrmode": self.IMP, "cycle": 4}),
                ("LDY", {"opcode": self.LDY, "addrmode": self.ABX, "cycle": 4}),
                ("LDA", {"opcode": self.LDA, "addrmode": self.ABX, "cycle": 4}),
                ("LDX", {"opcode": self.LDX, "addrmode": self.ABY, "cycle": 4}),
                ("???", {"opcode": self.XXX, "addrmode": self.IMP, "cycle": 4}),
                ("CPY", {"opcode": self.CPY, "addrmode": self.IMM, "cycle": 2}),
                ("CMP", {"opcode": self.CMP, "addrmode": self.IZX, "cycle": 6}),
                ("???", {"opcode": self.NOP, "addrmode": self.IMP, "cycle": 2}),
                ("???", {"opcode": self.XXX, "addrmode": self.IMP, "cycle": 8}),
                ("CPY", {"opcode": self.CPY, "addrmode": self.ZP0, "cycle": 3}),
                ("CMP", {"opcode": self.CMP, "addrmode": self.ZP0, "cycle": 3}),
                ("DEC", {"opcode": self.DEC, "addrmode": self.ZP0, "cycle": 5}),
                ("???", {"opcode": self.XXX, "addrmode": self.IMP, "cycle": 5}),
                ("INY", {"opcode": self.INY, "addrmode": self.IMP, "cycle": 2}),
                ("CMP", {"opcode": self.CMP, "addrmode": self.IMM, "cycle": 2}),
                ("DEX", {"opcode": self.DEX, "addrmode": self.IMP, "cycle": 2}),
                ("???", {"opcode": self.XXX, "addrmode": self.IMP, "cycle": 2}),
                ("CPY", {"opcode": self.CPY, "addrmode": self.ABS, "cycle": 4}),
                ("CMP", {"opcode": self.CMP, "addrmode": self.ABS, "cycle": 4}),
                ("DEC", {"opcode": self.DEC, "addrmode": self.ABS, "cycle": 6}),
                ("???", {"opcode": self.XXX, "addrmode": self.IMP, "cycle": 6}),
                ("BNE", {"opcode": self.BNE, "addrmode": self.REL, "cycle": 2}),
                ("CMP", {"opcode": self.CMP, "addrmode": self.IZY, "cycle": 5}),
                ("???", {"opcode": self.XXX, "addrmode": self.IMP, "cycle": 2}),
                ("???", {"opcode": self.XXX, "addrmode": self.IMP, "cycle": 8}),
                ("???", {"opcode": self.NOP, "addrmode": self.IMP, "cycle": 4}),
                ("CMP", {"opcode": self.CMP, "addrmode": self.ZPX, "cycle": 4}),
                ("DEC", {"opcode": self.DEC, "addrmode": self.ZPX, "cycle": 6}),
                ("???", {"opcode": self.XXX, "addrmode": self.IMP, "cycle": 6}),
                ("CLD", {"opcode": self.CLD, "addrmode": self.IMP, "cycle": 2}),
                ("CMP", {"opcode": self.CMP, "addrmode": self.ABY, "cycle": 4}),
                ("NOP", {"opcode": self.NOP, "addrmode": self.IMP, "cycle": 2}),
                ("???", {"opcode": self.XXX, "addrmode": self.IMP, "cycle": 7}),
                ("???", {"opcode": self.NOP, "addrmode": self.IMP, "cycle": 4}),
                ("CMP", {"opcode": self.CMP, "addrmode": self.ABX, "cycle": 4}),
                ("DEC", {"opcode": self.DEC, "addrmode": self.ABX, "cycle": 7}),
                ("???", {"opcode": self.XXX, "addrmode": self.IMP, "cycle": 7}),
                ("CPX", {"opcode": self.CPX, "addrmode": self.IMM, "cycle": 2}),
                ("SBC", {"opcode": self.SBC, "addrmode": self.IZX, "cycle": 6}),
                ("???", {"opcode": self.NOP, "addrmode": self.IMP, "cycle": 2}),
                ("???", {"opcode": self.XXX, "addrmode": self.IMP, "cycle": 8}),
                ("CPX", {"opcode": self.CPX, "addrmode": self.ZP0, "cycle": 3}),
                ("SBC", {"opcode": self.SBC, "addrmode": self.ZP0, "cycle": 3}),
                ("INC", {"opcode": self.INC, "addrmode": self.ZP0, "cycle": 5}),
                ("???", {"opcode": self.XXX, "addrmode": self.IMP, "cycle": 5}),
                ("INX", {"opcode": self.INX, "addrmode": self.IMP, "cycle": 2}),
                ("SBC", {"opcode": self.SBC, "addrmode": self.IMM, "cycle": 2}),
                ("NOP", {"opcode": self.NOP, "addrmode": self.IMP, "cycle": 2}),
                ("???", {"opcode": self.SBC, "addrmode": self.IMP, "cycle": 2}),
                ("CPX", {"opcode": self.CPX, "addrmode": self.ABS, "cycle": 4}),
                ("SBC", {"opcode": self.SBC, "addrmode": self.ABS, "cycle": 4}),
                ("INC", {"opcode": self.INC, "addrmode": self.ABS, "cycle": 6}),
                ("???", {"opcode": self.XXX, "addrmode": self.IMP, "cycle": 6}),
                ("BEQ", {"opcode": self.BEQ, "addrmode": self.REL, "cycle": 2}),
                ("SBC", {"opcode": self.SBC, "addrmode": self.IZY, "cycle": 5}),
                ("???", {"opcode": self.XXX, "addrmode": self.IMP, "cycle": 2}),
                ("???", {"opcode": self.XXX, "addrmode": self.IMP, "cycle": 8}),
                ("???", {"opcode": self.NOP, "addrmode": self.IMP, "cycle": 4}),
                ("SBC", {"opcode": self.SBC, "addrmode": self.ZPX, "cycle": 4}),
                ("INC", {"opcode": self.INC, "addrmode": self.ZPX, "cycle": 6}),
                ("???", {"opcode": self.XXX, "addrmode": self.IMP, "cycle": 6}),
                ("SED", {"opcode": self.SED, "addrmode": self.IMP, "cycle": 2}),
                ("SBC", {"opcode": self.SBC, "addrmode": self.ABY, "cycle": 4}),
                ("NOP", {"opcode": self.NOP, "addrmode": self.IMP, "cycle": 2}),
                ("???", {"opcode": self.XXX, "addrmode": self.IMP, "cycle": 7}),
                ("???", {"opcode": self.NOP, "addrmode": self.IMP, "cycle": 4}),
                ("SBC", {"opcode": self.SBC, "addrmode": self.ABX, "cycle": 4}),
                ("INC", {"opcode": self.INC, "addrmode": self.ABX, "cycle": 7}),
                ("???", {"opcode": self.XXX, "addrmode": self.IMP, "cycle": 7}),
            ]
        }

        return instructions
