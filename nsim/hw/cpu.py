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
from typing import Callable, Dict, List, Tuple

import numpy as np


# base address of stack in memory
STACK_ADDR: int = 0x0100
# address for initial address pointer
INIT_ADDR: int = 0xFFFC
# address for interrupt options to load codes from
INTR_ADDR: int = 0xFFFE
NMI_ADDR: int = 0xFFFA
# resetting the CPU takes time, and this is a hardcoded cycle count
RESET_TIME: int = 8
INTR_TIME: int = 7
NMI_TIME: int = 8


@dataclass
class FLAGS6502:
    """Flags in 6502 processor. Each register is a bit."""

    C: int = 0  # carry bit
    Z: int = 0  # zero
    I: int = 0  # disable interrupts
    D: int = 0  # decimal mode (disabled in this implementation, as does nes)
    B: int = 0  # break
    U: int = 0  # unused
    V: int = 0  # overflow
    N: int = 0  # negative (used when using signed variables)

    def extract(self) -> int:
        """Convert all flags into an 8-bit value.
        Returns a byte.
        """
        flags: int = (
            self.C
            << 0 + self.Z
            << 1 + self.I
            << 2 + self.D
            << 3 + self.B
            << 4 + self.U
            << 5 + self.V
            << 6 + self.N
            << 7
        )
        return flags

    def apply(self, value: int):
        """Load a byte and apply it to all eight registers."""
        self.C = value & 0b00000001
        self.Z = value & 0b00000010
        self.I = value & 0b00000100
        self.D = value & 0b00001000
        self.B = value & 0b00010000
        self.U = value & 0b00100000
        self.V = value & 0b01000000
        self.N = value & 0b10000000

    def print_flags(self):
        """Debugging function to print registers."""
        print(self.C, self.Z, self.I, self.D, self.B, self.U, self.V, self.N)


class SY6502:
    @dataclass
    class Instruction:
        name: str
        opcode: Callable
        addrmode: Callable
        cycle: int = 0

    def __init__(self, cpu_ram: np.ndarray, ppu_ram: np.ndarray):
        # map memory devices
        self.cpu_ram: np.ndarray = cpu_ram
        self.ppu_ram: np.ndarray = ppu_ram

        # setup flags
        self.flags: FLAGS6502 = FLAGS6502()
        # setup registers
        self.a: int = 0x00  # accumulator register
        self.x: int = 0x00  # X register
        self.y: int = 0x00  # Y register
        self.stkp: int = 0x00  # stack pointer        self.pc: int = 0x0000  # program counter, stores an address
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

    def cpu_read(self, addr: int, readonly: bool = False) -> int:
        """Read a 2-byte address and return a single byte value."""
        if 0x0000 <= addr <= 0x1FFF:
            data: int = self.cpu_ram[addr & 0x07FF]  # ram mirror IO
            #data: int = self.cpu_ram[addr]  # ram mirror IO
        return data

    def cpu_write(self, addr: int, data: int):
        """Write a byte of data to a 2-byte addr."""
        if 0x0000 <= addr <= 0x1FFF:
            self.cpu_ram[addr & 0x07FF] = data
            #self.cpu_ram[addr] = data

    def read_flag():
        """Read a specific flag value."""

    def set_flag():
        """Overwrite a flag value."""

    def clock(self):
        """Clock function."""
        if self.cycle == 0:
            # read the next opcode, which is 1-byte
            opcode: int = self.cpu_read(addr=self.pc)
            # update address
            self.pc += 1

            # always set unused flag to 1
            self.flags.U = 1

            # pointer to dataclass
            instruction: self.Instruction = self.instructions[opcode]

            # using this opcode to get required cycle count
            new_cycle: int = instruction.cycle
            # call the address mode function
            # will return 1 if it requires additional cycles or 0 if not
            add_cycle_address: int = instruction.addrmode()

            # call the operate function
            # will return 1 if it requires additional cycles or 0 if not
            add_cycle_operation: int = instruction.opcode()

            # if either operation or address mode requires additional cycles,
            # we add that to cycle count
            new_cycle += add_cycle_address & add_cycle_operation
            # update in-class variable
            self.cycle = new_cycle

        # decrease cycle count
        self.cycle -= 1

    def complete(self) -> bool:
        return self.cycle == 0

    def reset(self):
        """Reset signal. Interrupts the processor after current cycle.
        Reset the CPU into null state.
        """
        self.a = 0
        self.x = 0
        self.y = 0
        self.stkp = 0xFD
        self.status = 0x00 | self.flags.U

        # here we use a non-0x00 address to reset address memory, this is
        # because at that 0 location there may not be codes for execution.
        # Instead, 6502 uses address 0xFFFC as the initial address for code
        # loading.
        addr = INIT_ADDR
        # now load the address at that location
        print(addr, hex(addr))
        lower: int = self.cpu_read(addr)
        higher: int = self.cpu_read(addr + 1)
        self.pc = (higher << 8) | lower

        # reset other internal variables
        self.addr_rel = 0x0000
        self.addr_abs = 0x0000
        self.fetched = 0x00

        self.cycle = RESET_TIME

    def irq(self):
        """Interrupt request. Interrupts the processor after current cycle.
        May be ignored if flags disables this function.

        When an interrupt occurs, it will save the current program state to
        stack.
        """
        if self.flags == 0:
            # save the current program counter to stack
            # it takes two operations because it's a 2-byte variable
            self.cpu_write(  # write the higher byte to lower address location
                addr=STACK_ADDR + self.stkp, data=(self.pc >> 8) & 0x00FF
            )
            self.stkp -= 1
            self.cpu_write(  # write lower byte to higher address location
                addr=STACK_ADDR + self.stkp, data=(self.pc & 0x00FF)
            )
            self.stkp -= 1

            # we also write status register/flags to stack
            self.flags.B = 0  # break flag
            self.flags.U = 1  # unused flag
            self.flags.I = 1  # disables interrupt flag
            self.cpu_write(addr=STACK_ADDR + self.stkp, data=self.flags.extract())
            self.stkp -= 1

            # set code address to the pre-defined location
            addr: int = INTR_ADDR
            lower: int = self.cpu_read(addr=addr)
            higher: int = self.cpu_read(addr=addr + 1)
            self.pc = (higher << 8) | lower

            # add cycle overhead
            self.cycle = INTR_TIME

    def nmi(self):
        """Non-maskable interrupt request signal. Interrupts the processor after
        current cycle. This interrupt signal cannot be ignored.
        This is the same function as irq(). Except it cannot be ignored.
        """
        self.cpu_write(  # write the higher byte to lower address location
            addr=STACK_ADDR + self.stkp, data=(self.pc >> 8) & 0x00FF
        )
        self.stkp -= 1
        self.cpu_write(  # write lower byte to higher address location
            addr=STACK_ADDR + self.stkp, data=(self.pc & 0x00FF)
        )
        self.stkp -= 1

        # we also write status register/flags to stack
        self.flags.B = 0  # break flag
        self.flags.U = 1  # unused flag
        self.flags.I = 1  # disables interrupt flag
        self.cpu_write(addr=STACK_ADDR + self.stkp, data=self.flags.extract())
        self.stkp -= 1

        # set code address to the pre-defined location
        addr: int = NMI_ADDR
        lower: int = self.cpu_read(addr=addr)
        higher: int = self.cpu_read(addr=addr + 1)
        self.pc = (higher << 8) | lower

        # add cycle overhead
        self.cycle = NMI_TIME

    def fetch(
        self,
    ) -> int:
        """Fetch data from addressable memory. This returns an 8-bit."""
        # an exception is implicit (IMP) function who does not return a value.
        if self.instructions[self.opcode].addrmode != self.IMP:
            fetched: int = self.cpu_read(self.addr_abs)

            self.fetched = fetched
            return fetched
        return

    def _jump(self):
        """Common codes used in many branching functions.
        Therefore it's refactored here.
        """
        # branching requires an additional cycle
        self.cycle += 1

        # python would somehow cast this 16-bit int to 32-bit range, and
        # therefore we need to mask it
        self.addr_abs = (self.pc + self.addr_rel) & 0xFFFF  # jump with offset

        # if the page cross the page, it would require yet another cycle
        # NOTE: all branching operations would need to check if page changes
        # and add additional cycle if so
        if (self.addr_abs & 0xFF00) != (self.pc & 0xFF00):
            self.cycle += 1

        self.pc = self.addr_abs

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
        self.addr_abs = self.pc
        self.pc += 1
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
        self.addr_abs = self.cpu_read(self.pc)
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
        self.addr_abs = self.cpu_read(self.pc) + self.x
        self.pc += 1
        self.addr_abs &= 0x00FF
        return 0

    def ZPY(self) -> int:
        """Addressing mode.
        Zero-page addressing with value in Y register being used as offset."""
        self.addr_abs = self.cpu_read(self.pc) + self.y
        self.pc += 1
        self.addr_abs &= 0x00FF
        return 0

    def REL(self) -> int:
        """Addressing mode.
        Relative addressing. Only used in branching operations.
        The jump range can only be within -128 to +127 byte. Since this includes
        a negative number, who usually has its first bit, or bit 7 set to 1.
        A check is written to
        NOTE: this one I don't quite understand.
        """
        addr: int = self.cpu_read(self.pc)
        self.pc += 1
        if addr & 0x80:  # check if it's a negative number
            # if true (negative), set high byte of relative address to ones
            # this works out for the binary arithmetic (but why??)
            addr |= 0xFF00
        self.addr_rel = addr
        return 0

    def ABS(self) -> int:
        """Addressing mode.
        Absolute addressing. The second byte of instruction is the offset of the
        next effective address, and the third byte is the page. This forms a
        16-bit address location which has the full 64KB range."""
        lower: int = self.cpu_read(self.pc)  # load lower part
        self.pc += 1  # increase address to reach the next byte
        higher: int = self.cpu_read(self.pc)  # and read the higher part
        self.pc += 1  # increase again
        self.addr_abs = (higher << 8) | lower  # combine them
        return 0

    def ABX(self) -> int:
        """Addressing mode.
        Absolute addressing with X added to the address that
        is contained in the second and third byte."""
        lower: int = self.cpu_read(self.pc)
        self.pc += 1
        higher: int = self.cpu_read(self.pc)
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
        lower: int = self.cpu_read(self.pc)
        self.pc += 1
        higher: int = self.cpu_read(self.pc)
        self.pc += 1

        _addr_abs: int = (higher << 8) | lower  # form the base address
        _addr_abs += self.y  # offset it by content in y register
        self.addr_abs = _addr_abs  # this may cause overflow (dealt below)

        if _addr_abs & 0xFF00 != (higher << 8):
            return 1
        return 0

    def IND(self) -> int:
        """Addressing mode.
        Indirect addressing. No official docs found. Guessing it uses the second
        and third byte to form lower and higher byte of a pointer, and we need
        to get that address.
        (This is a pointer implementation)
        """
        p_lower: int = self.cpu_read(self.pc)
        self.pc += 1
        p_higher: int = self.cpu_read(self.pc)
        self.pc += 1

        # combine lower and higher to form address of the pointer
        pointed_addr: int = (p_higher << 8) | p_lower
        # read content that is pointed
        lower: int = self.cpu_read(pointed_addr)
        if lower == 0x00FF:
            # this is a hardware bug of 6502, if the pointer's address would
            # cause a carry after increment, then the page should be turned, but
            # the hardware does not do that. Here we emulate that bug as well.
            high_addr: int = pointed_addr & 0xFF00
        else:
            high_addr = pointed_addr + 1
        higher: int = self.cpu_read(high_addr)

        # form that address pointed by pointer
        self.addr_abs = (higher << 8) | lower
        return 0

    def IZX(self) -> int:
        """Addressing mode.
        Indirect addressing. NOTE: this is note an equivalent to indirect Y.
        The next byte plus value in register x forms the lower byte of an
        address on page zero. The carry is discarded. Then that address plus its
        next one forms the desired address.
        """
        # first pointer address that forms the lower part of desired address
        value: int = self.cpu_read(self.pc)
        self.pc += 1
        lower_addr: int = (value + self.x) & 0x00FF
        # this way we discard carry
        higher_addr: int = (value + self.x + 1) & 0x00FF

        self.addr_abs = (self.cpu_read(higher_addr) << 8) | self.cpu_read(lower_addr)
        return 0

    def IZY(self) -> int:
        """Addressing mode.
        Indirect addressing. The second byte of the instruction is an offset on
        page zero, and the content of this address is added to value in register
        y; and this forms lower eight bits of address. The carry of that
        addition operation is then added to the next zero-page address and forms
        the higher eight bits of address.

        NOTE: The actual implementation doesn't really reflect what's described
        above, but...
        """
        # read offset location of the pointer
        value: int = self.cpu_read(self.pc)
        self.pc += 1

        lower: int = self.cpu_read(value & 0x00FF)
        higher: int = self.cpu_read((value + 1) & 0x00FF)

        addr: int = higher << 8 | lower
        addr += self.y

        if (addr & 0xFF00) != (higher << 8):
            return 1
        return 0

    # Opcode section (totally 56)
    def ADC(self) -> int:
        """Opcode function.
        Addition function. Add values in accumulator with fetched one, plus
        carry.
        This is a rather complex function because sometimes programmer would
        want to use signed numbers (-128 to 127) rather than unsigned ones
        (0 to 255). Therefore an example as unsigned number 132 can be
        mistakenly treated as -124 in signed manner (overflow).
        Dealing with negative numbers doesn't require special hardware as maths
        still works out (computer organization).
        6502 has two flags to help signed addition operations:
        1. If the most significant bit is 1, it can be a negative number

        Adding two signed 8-bit numbers (-128 to 127) may result an overflow;
        Adding a positive 8-bit and a negative 8-bit will never overflow.
        Adding two signed negative numbers may also cause overflow.
        Therefore, the "V" register in flag register also helps when two signed
        numbers are added.

        A truth table can help (0, 1 are the most significant bit of that
        number):

                A   M   R   V     A^R ~A^M    &
                0   0   0   0      0    1     0
                0   0   1   1      1    1     1
                0   1   0   0      0    0     0
                0   1   1   1      1    0     0
                1   0   0   0      1    0     0
                1   0   1   1      0    0     0
                1   1   0   0      1    1     1
                1   1   1   1      0    1     0

        where A is the number in accumulator, M is fetched number, and R is the
        result. V is the overflow flag, and A^R is exclusive-or.
        We can there are only two situations where overflow should be set, which
        can be calculated by using binary "and" between XOR(A, R) and ~XOR(A, M)
        """
        self.fetch()
        # here we perform the addition in the convenient 16-bit domain.
        temp: int = self.a + self.fetched + self.flags.C  # carry
        # set carry flag if result exceeds 8-bit domain
        self.flags.C = temp > 255
        # set zero flag just as it was before (???)
        self.flags.Z = (temp & 0x00FF) == 0
        # the carry flag should be the most significant bit of low byte
        self.flags.N = temp & 0x80
        # now the overflow flag
        xor_result: int = self.a ^ temp
        not_xor_result: int = ~(self.a ^ self.fetched)
        self.flags.V = (xor_result & not_xor_result) & 0x0080
        # save back the result to accumulator (after filtering out higher byte)
        self.a = temp & 0x00FF
        return 1

    def AND(self) -> int:
        """Opcode function.
        Bit-wise and function. Is a foundation of all other functions.
        It's a bit-wise "and" between the accumulator and the fetched value.
        """
        self.fetch()
        self.a = self.a & self.fetched

        # set flags
        self.flags.Z = self.a == 0x00  # update status register as required
        self.flags.N = self.a & 0x80  # set zero flag
        return 1

    def ASL(self) -> int:
        """Opcode function.
        Arithmetic shift left.
        """
        self.fetch()
        temp: int = self.fetched << 1
        self.flags.C = (temp & 0xFF00) > 0
        self.flags.Z = (temp & 0x00FF) == 0x00
        self.flags.N = temp & 0x80
        if self.instructions[self.opcode].addrmode == self.IMP:
            self.a = temp & 0x00FF
        else:
            self.cpu_write(addr=self.addr_abs, data=temp & 0x00FF)
        return 0

    def BCC(self) -> int:
        """Opcode function.
        Branch on carry clear.
        """
        if self.flags.C == 0:
            self.cycle += 1
            self.addr_abs = self.pc + self.addr_rel

            # Page turned, requiring additional cycle.
            if self.addr_abs & 0xFF00 != self.pc & 0xFF00:
                self.cycle += 1

            self.pc = self.addr_abs
        return 0

    def BCS(self) -> int:
        """Opcode function.
        Branch-if-status-register-carry-is-set function.
        """
        if self.flags.C == 1:  # get carry flag
            self._jump()
        return 0

    def BEQ(self) -> int:
        """Opcode function.
        Branch if equal.
        """
        # Z is the zero register
        if self.flags.Z == 1:
            self._jump()
        return 0

    def BIT(self) -> int:
        """Opcode function.
        Tests bits in memory with accumulator.
        """
        self.fetch()
        temp: int = self.a & self.fetched
        self.flags.Z = (temp & 0x00FF) == 0x00
        self.flags.N = self.fetched & (1 << 7)
        self.flags.V = self.fetched & (1 << 6)

        return 0

    def BMI(self) -> int:
        """Opcode function.
        Branch if result is negative.
        """
        if self.flags.N == 1:
            self._jump()
        return 0

    def BNE(self) -> int:
        """Opcode function.
        Branch if result is not equal (result is not zero).
        """
        if self.flags.Z == 0:
            self._jump()
        return 0

    def BPL(self) -> int:
        """Opcode function.
        Branch if result is positive.
        """
        if self.flags.N == 0:
            self._jump()
        return 0

    def BRK(self) -> int:
        """Opcode function.
        Force break. Program sourced interrupt."""
        self.pc += 1

        self.flags.I = 1
        self.cpu_write(addr=STACK_ADDR + self.stkp, data=(self.pc >> 8) & 0x00FF)
        self.stkp -= 1
        self.cpu_write(addr=STACK_ADDR + self.stkp, data=self.pc & 0x00FF)
        self.stkp -= 1

        self.flags.B = 1  # Break flag
        self.cpu_write(addr=STACK_ADDR + self.stkp, data=self.status)
        self.stkp -= 1
        self.flags.B = 0

        self.pc = self.cpu_read(INTR_ADDR) | (self.cpu_read(0xFFFF) << 8)
        return 0

    def BVC(self) -> int:
        """Opcode function.
        Branch on overflow clear.
        """
        if self.flags.V == 0:
            self._jump()
        return 0

    def BVS(self) -> int:
        """Opcode function.
        Branch on overflow set.
        """
        if self.flags.V == 1:
            self._jump()
        return 0

    def CLC(self) -> int:
        """Opcode function.
        Clear carry function.
        """
        self.flags.C = 0  # clear the carry flag
        return 0

    def CLD(self) -> int:
        """Opcode function.
        Clear decimal mode function."""
        self.flags.D = 0
        return 0

    def CLI(self) -> int:
        """Opcode function.
        Clear disable-interrupts function.
        """
        self.flags.I = 0
        return 0

    def CLV(self) -> int:
        """Opcode function.
        Clear overflow flag function.
        """
        self.flags.V = 0
        return 0

    def CMP(self) -> int:
        """Opcode function.
        Compare memory and accumulator.
        """
        self.fetch()
        # Note that we cast these values into a 16-bit space
        temp: int = self.a - self.fetched
        self.flags.C = temp >= 0  # Carry flag
        self.flags.Z = (temp & 0x00FF) == 0x0000  # Zero flag
        self.flags.N = temp & 0x0080  # Negative flag
        return 0

    def CPX(self) -> int:
        """Opcode function.
        Compare memory and x register."""
        self.fetch()
        # Note that we cast these values into a 16-bit space
        temp: int = self.x - self.fetched
        self.flags.C = temp >= 0  # Carry flag
        self.flags.Z = (temp & 0x00FF) == 0x0000  # Zero flag
        self.flags.N = temp & 0x0080  # Negative flag
        return 0

    def CPY(self) -> int:
        """Opcode function.
        Compare memory and y register."""
        self.fetch()
        # Note that we cast these values into a 16-bit space
        temp: int = self.y - self.fetched
        self.flags.C = temp >= 0  # Carry flag
        self.flags.Z = (temp & 0x00FF) == 0x0000  # Zero flag
        self.flags.N = temp & 0x0080  # Negative flag
        return 0

    def DEC(self) -> int:
        """Opcode function.
        Decrease memory value by one.
        """
        self.fetch()
        temp: int = self.fetched - 1
        self.cpu_write(addr=self.addr_abs, data=temp & 0x00FF)
        self.flags.Z = (temp & 0x00FF) == 0x0000
        self.flags.N = temp & 0x0080
        return 0

    def DEX(self) -> int:
        """Opcode function.
        Decrease value in x register by one."""
        self.x -= 1
        self.flags.Z = self.x == 0x00
        self.flags.N = self.x & 0x80
        return 0

    def DEY(self) -> int:
        """Opcode function.
        Decrease value in y register by one."""
        self.y -= 1
        self.flags.Z = self.y == 0x00
        self.flags.N = self.y & 0x80
        return 0

    def EOR(self) -> int:
        """Opcode function.
        xor operation on accumulator and memory.
        """
        self.fetch()
        self.a = self.a ^ self.fetched
        self.flags.Z = self.a == 0x0000
        self.flags.N = self.a & 0x0080
        return 0

    def INC(self) -> int:
        """Opcode function.
        Increase value in memory by one.
        """
        self.fetch()
        temp: int = self.fetched + 1  # 16-bit space
        self.cpu_write(addr=self.addr_abs, data=temp & 0x00FF)
        self.flags.Z = (temp & 0x00FF) == 0x0000
        self.flags.N = temp & 0x0080
        return 0

    def INX(self) -> int:
        """Opcode function.
        Increase value of x register by one.
        """
        temp: int = self.x + 1  # 16-bit space
        self.x = temp & 0x00FF
        self.flags.Z = (temp & 0x00FF) == 0x0000
        self.flags.N = temp & 0x0080
        return 0

    def INY(self) -> int:
        """Opcode function
        Increase value of y register by one.
        """
        temp: int = self.y + 1  # 16-bit space
        self.y = temp & 0x00FF
        self.flags.Z = (temp & 0x00FF) == 0x0000
        self.flags.N = temp & 0x0080
        return 0

    def JMP(self) -> int:
        """Opcode function.
        Jump to new location.
        """
        self.pc = self.addr_abs
        return 0

    def JSR(self) -> int:
        """Opcode function.
        Jump to new location and save return address to stack.
        """
        self.pc -= 1
        self.cpu_write(  # write the higher byte to lower address location
            addr=STACK_ADDR + self.stkp, data=(self.pc >> 8) & 0x00FF
        )
        self.stkp -= 1
        self.cpu_write(  # write lower byte to higher address location
            addr=STACK_ADDR + self.stkp, data=(self.pc & 0x00FF)
        )
        self.stkp -= 1

        self.pc = self.addr_abs
        return 0

    def LDA(self) -> int:
        """Opcode function.
        Load accumulator with value in memory."""
        self.fetch()
        self.a = self.fetched
        self.flags.Z = self.a == 0x00
        self.flags.N = self.a & 0x80
        return 1

    def LDX(self) -> int:
        """Opcode function.
        Load x with value in memory."""
        self.fetch()
        self.x = self.fetched
        self.flags.Z = self.x == 0x00
        self.flags.N = self.x & 0x80
        return 1

    def LDY(self) -> int:
        """Opcode function.
        Load y with value in memory."""
        self.fetch()
        self.y = self.fetched
        self.flags.Z = self.y == 0x00
        self.flags.N = self.y & 0x80
        return 1

    def LSR(self) -> int:
        """Opcode function.
        Shift one bit right (accumulator or memory).
        """
        self.fetch()
        self.flags.C = self.fetched & 0x0001
        temp: int = self.fetched >> 1
        self.flags.Z = (temp & 0x00FF) == 0x0000
        self.flags.N = temp & 0x0080

        if self.instructions[self.opcode].addrmode == self.IMP:
            self.a = temp & 0x00FF
        else:
            self.cpu_write(self.addr_abs, temp & 0x00FF)
        return 0

    def NOP(self) -> int:
        """Opcode function.
        No operation. Not all "no operation" are equal.
        Some can be found at https://wiki.nesdev.com/w/index.php/CPU_unofficial_opcodes
        Not all are implemented here.
        """
        if self.opcode in [0x1C, 0x3C, 0x5C, 0x7C, 0xDC, 0xFC]:
            return 1
        return 0

    def ORA(self) -> int:
        """Opcode function.
        Bit-wise or operation between accumulator and value in memory."""
        self.fetch()
        self.a = self.a | self.fetched
        self.flags.Z = self.a == 0x00
        self.flags.N = self.a & 0x80

        return 0

    def PHA(self) -> int:
        """Opcode function.
        Pushes the accumulator to the stack.
        Note that the stack exists in RAM and therefore we need to call the
        memory-modifying function to do that.
        """
        self.cpu_write(addr=STACK_ADDR + self.stkp, data=self.a)
        self.stkp -= 1
        return 0

    def PHP(self) -> int:
        """Opcode function.
        Push status register to stack.
        """
        self.cpu_write(
            addr=STACK_ADDR + self.stkp, data=self.status | self.flags.B | self.flags.U
        )
        self.stkp -= 1
        self.flags.B = 0
        self.flags.U = 0
        return 0

    def PLA(self) -> int:
        """Opcode function.
        Pop the stack.
        """
        self.stkp += 1
        self.a = self.cpu_read(addr=STACK_ADDR + self.stkp)
        self.flags.Z = self.a == 0x00
        self.flags.N = self.a & 0x80
        return 0

    def PLP(self) -> int:
        """Opcode function.
        Pop stack to status register.
        """
        self.stkp += 1
        self.status = self.cpu_read(addr=STACK_ADDR + self.stkp)
        self.flags.U = 1  # Unused register
        return 0

    def ROL(self) -> int:
        """Opcode function.
        Rotate one bit left (memory or accumulator).
        """
        self.fetch()
        temp: int = self.fetched << 1 | self.flags.C
        self.flags.C = temp & 0xFF00
        self.flags.Z = (temp & 0x00FF) == 0x0000
        self.flags.N = temp & 0x0080

        if self.instructions[self.opcode] == self.IMP:
            self.a = temp & 0x00FF
        else:
            self.cpu_write(addr=self.addr_abs, data=temp & 0x00FF)
        return 0

    def ROR(self) -> int:
        """Opcode function.
        Rotate one bit right (memory or accumulator).
        """
        self.fetch()
        # Note it shifts left by 7
        temp: int = self.fetched >> 1 | (self.flags.C << 7)
        self.flags.C = self.fetched & 0x01
        self.flags.Z = (temp & 0x00FF) == 0x0000
        self.flags.N = temp & 0x0080

        if self.instructions[self.opcode] == self.IMP:
            self.a = temp & 0x00FF
        else:
            self.cpu_write(addr=self.addr_abs, data=temp & 0x00FF)
        return 0

    def RTI(self) -> int:
        """Opcode function.
        Restore processor before interruption occurred.
        """
        self.stkp += 1
        self.status: int = self.cpu_read(STACK_ADDR + self.stkp)
        self.status &= ~self.flags.B
        self.status &= ~self.flags.U

        self.stkp += 1
        self.pc = self.cpu_read(STACK_ADDR + self.stkp)
        self.stkp += 1
        self.pc |= self.cpu_read(STACK_ADDR + self.stkp) << 8

        return 0

    def RTS(self) -> int:
        """Opcode function.
        Return from subroutine.
        """
        self.stkp += 1
        self.pc = self.cpu_read(STACK_ADDR + self.stkp)
        self.stkp += 1
        self.pc |= self.cpu_read(STACK_ADDR + self.stkp) << 8

        self.pc += 1
        return 0

    def SBC(self) -> int:
        """Opcode function.
        Subtraction function. It updates accumulator with the result of
        accumulator - fetched - (1 - carry); where the last item is the
        opposite of carry bit, because in this case it's a "borrow" bit.

        It is wise for hardware designers to reuse existing implementation, and
        in this case, we can convert this subtraction operation into addition.
        We don't know if 6502 uses its addition module to perform subtraction.

        A = A - M - (1 - C) becomes A + (-1) * (M - (1 - C))
        then, A = A + (- M) + 1 + C
        and when flipping the sign of a signed number, we invert each bit and
        plus one. E.g.
        5 = 0b00000101 and -5 = 0b11111010 + 0b00000001
        Note that plus one operation can be included in the above deduced
        formula, so for this subtraction operation, all we need to do is to
        invert the number and use the addition function (ADC) codes.
        """
        self.fetch()
        # we can use the 16-bit space for our convenience
        # use xor function to invert the last 8 bits
        value: int = self.fetched ^ 0x00FF
        # after this operation, it's identical to addition function

        temp: int = self.a + value + self.flags.C
        self.flags.C = temp & 0xFF00
        self.flags.Z = (temp & 0x00FF) == 0
        self.flags.N = temp & 0x80
        # now the overflow flag
        self.flags.V = ((temp ^ self.a) & (temp ^ value)) & 0x0080
        self.a = temp & 0x00FF
        return 1

    def SEC(self) -> int:
        """Opcode function.
        Set carry flag.
        """
        self.flags.C = 1
        return 0

    def SED(self) -> int:
        """Opcode function.
        Set decimal flag.
        """
        self.flags.D = 1
        return 0

    def SEI(self) -> int:
        """Opcode function.
        Set interrupt-disabled flag (enables interrupt).
        """
        self.flags.I = 1
        return 0

    def STA(self) -> int:
        """Opcode function.
        Store accumulator to memory.
        """
        self.cpu_write(addr=self.addr_abs, data=self.a)
        return 0

    def STX(self) -> int:
        """Opcode function.
        Store x register value to memory.
        """
        self.cpu_write(addr=self.addr_abs, data=self.x)
        return 0

    def STY(self) -> int:
        """Opcode function.
        Store y register value to memory.
        """
        self.cpu_write(addr=self.addr_abs, data=self.y)
        return 0

    def TAX(self) -> int:
        """Opcode function.
        Transfer accumulator to x register.
        """
        self.x = self.a
        self.flags.Z = self.x == 0x00
        self.flags.N = self.x & 0x80
        return 0

    def TAY(self) -> int:
        """Opcode function.
        Transfer accumulator to y register.
        """
        self.y = self.a
        self.flags.Z = self.y == 0x00
        self.flags.N = self.y & 0x80
        return 0

    def TSX(self) -> int:
        """Opcode function.
        Transfer stack pointer to x register.
        """
        self.x = self.stkp
        self.flags.Z = self.x == 0x00
        self.flags.N = self.x & 0x80
        return 0

    def TXA(self) -> int:
        """Opcode function.
        Transfer value in x register to accumulator.
        """
        self.a = self.x
        self.flags.Z = self.a == 0x00
        self.flags.N = self.a & 0x80
        return 0

    def TXS(self) -> int:
        """Opcode function.
        Transfer value in x register to stack pointer.
        """
        self.stkp = self.x
        return 0

    def TYA(self) -> int:
        """Opcode function.
        Transfer value in y register to accumulator.
        """
        self.a = self.y
        self.flags.Z = self.a == 0x00
        self.flags.N = self.a & 0x80
        return 0

    def XXX(self) -> int:
        """Special illegal opcode catcher."""
        return 0

    def disassemble(
        self,
        start: int,
        end: int,
    ) -> Dict[int, str]:
        """Disassembler function to convert binary instructions into strings.

        Args:
            start: Start address location.
            end: End address location.

        Returns:
            Dict[int, str]: Dictionary with addresses as keys and string
                instructions as values.
        """
        addr: int = start  # The address can be a 32-bit integer.
        padding: int = 0

        if start < 0:
            padding = abs(start)
            end += padding // 4
            addr = 0x00

        value: int = 0x00  # These three variables are 8-bit.
        map: Dict[int, str] = {}  # maps a 16-bit value to a string
        map[-1] = "\u2028" * (padding // 4)

        line_addr: int = 0x0000

        # Read from starting address a byte (instruction), and
        while addr <= end:
            line_addr = addr
            # create a string with address
            s_inst: str = "$" + f"{addr:0{4}X}" + ": "

            # then read instruction and acquire its name
            opcode: int = self.cpu_read(addr=addr, readonly=True)
            addr += 1
            # pointer to current instruction
            instruction: self.Instruction = self.instructions[opcode]
            # append instruction name to string
            s_inst += instruction.name + " "

            # pointer to addrmode function
            addrmode: Callable = instruction.addrmode
            # based on different address modes
            if addrmode == self.IMP:
                s_inst += " {IMP}"
            elif addrmode == self.IMM:
                value: int = self.cpu_read(addr=addr, readonly=True)
                addr += 1
                s_inst += "#$" + f"{value:0{2}X}" + " {IMM}"
            elif addrmode in [self.ZP0, self.ZPX, self.ZPY, self.IZX, self.IZY]:
                lo: int = self.cpu_read(addr=addr, readonly=True)
                hi: int = 0x00
                addr += 1
                s_inst += "$" + f"{lo:0{2}X} {addrmode.__name__}"
            elif addrmode in [self.ABS, self.ABX, self.ABY, self.IND]:
                lo = self.cpu_read(addr=addr, readonly=True)
                addr += 1
                hi = self.cpu_read(addr=addr, readonly=True)
                addr += 1
                s_inst += "$" + f"{((hi << 8) | lo):0{4}X}" + f" {addrmode.__name__}"
            elif addrmode == self.REL:
                value = self.cpu_read(addr=addr, readonly=True)
                addr += 1
                s_inst += "$" + f"{value:0{2}X}" + f" [${addr+value:0{4}X}]" + " {REL}"

            if self.pc == addr:
                s_inst = "> " + s_inst
            else:
                s_inst = "  " + s_inst

            map[line_addr] = s_inst
        return map

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
