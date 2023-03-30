"""Debugger window showing memory and dissembler."""
from typing import Callable, Dict, List
from pathlib import Path

import pyglet
import pyglet.window.key as key

from nsim.hw.cpu import SY6502


WIN_WIDTH: int = 900
WIN_HEIGHT: int = 600

RIGHT_X: int = int((WIN_WIDTH // 2) * 1.2)  # right column starting x

MEM_DISP_COLS: int = 16  # number of columns to display raw memory hex

# how many lines to show before and after current pc address
DISBLR_BEFOR: int = 14
DISBLR_AFTER: int = 24

DSBLR_HEIGHT: int = WIN_HEIGHT * 0.82

file_path: Path = Path(__file__)
pyglet.font.add_file(
    str(file_path.parent.joinpath("../assets/Perfect DOS VGA 437.ttf"))
)


class Debugger(pyglet.window.Window):
    def __init__(self, cpu: SY6502):
        super(Debugger, self).__init__(
            WIN_WIDTH, WIN_HEIGHT, resizable=False, fullscreen=False, caption="DEBUGGER"
        )
        # pointer to interested CPU instance
        self.cpu: SY6502 = cpu
        # inject debugging codes
        self.dbg_start: int
        self.load_debugging_program()

        # a batch renders stuffs together in a more efficient way
        self.batch = pyglet.graphics.Batch()
        self.draw_views()

        pyglet.clock.schedule_interval(self.update, 1 / 30)

    def draw_views(self):
        self.clear()
        del self.batch
        self.batch = pyglet.graphics.Batch()
        # these four views are all connected to the above batch object
        # create view for page zero in memory
        self.add_page_zero_view()
        # view for another page in memory
        self.add_page_view()
        # view for cpu registers
        self.add_register_view()
        # view for disassembler
        self.add_disassembler_view()
        # view for debugger operation hints
        self.add_info_view()

    def update(self, dt):
        # self.clear()
        self.draw()

    def on_key_press(self, symbol, modifiers):
        """Key pressing interactions."""
        if symbol == key.C:
            self.cpu.clock()
            while not self.cpu.complete():
                self.cpu.clock()
        elif symbol == key.R:
            self.cpu.reset()
        elif symbol == key.I:
            self.cpu.irq()
        elif symbol == key.N:
            self.cpu.nmi()
        elif symbol == key.D:
            self.close()

        self.draw_views()

        return

    def draw(self):
        self.clear()
        self.batch.draw()

    def get_memory_values(self, start_addr: int, end_addr: int) -> List[str]:
        """Convert requested range of memory into strings. Inclusive range."""
        mem_strs: List[str] = []
        hexify: Callable = lambda h: f"{h:0{2}X}"

        s_raw: str
        for i, value in enumerate(self.cpu.bus.cpu_ram[start_addr : end_addr + 1]):
            # col limit reached
            if i % MEM_DISP_COLS == 0:
                if i > 0:  # append last line and form a new line
                    mem_strs.append(s_raw)
                s_raw = "$" + f"{start_addr + i:0{4}X}" + ":  "
            # add individual element into current line
            s_raw += hexify(value) + " "
            # last address in memory range
            if i == end_addr - start_addr:
                mem_strs.append(s_raw)
        return mem_strs

    def add_page_zero_view(self):
        """Add page-zero memory view."""
        mem_strings: List[str] = self.get_memory_values(0, 0x00FF)
        mem_str: str = "\u2028".join(mem_strings)
        document = pyglet.text.document.FormattedDocument(mem_str)
        document.set_style(
            0,
            len(mem_str),
            dict(color=(255, 255, 255, 255), font_name="Perfect DOS VGA 437"),
        )
        self.page0_text = pyglet.text.layout.TextLayout(
            document, multiline=True, wrap_lines=False, batch=self.batch
        )

        # location related
        self.page0_text.x = 0
        self.page0_text.y = WIN_HEIGHT
        self.page0_text.anchor_y = "top"

    def add_page_view(self):
        """Add a random page memory view."""
        mem_strings: List[str] = self.get_memory_values(
            self.dbg_start, self.dbg_start + 0xFF)
        mem_str: str = "\u2028".join(mem_strings)
        document = pyglet.text.document.FormattedDocument(mem_str)
        document.set_style(
            0,
            len(mem_str),
            dict(color=(255, 255, 255, 255), font_name="Perfect DOS VGA 437"),
        )
        self.pager_text = pyglet.text.layout.TextLayout(
            document, multiline=True, wrap_lines=False, batch=self.batch
        )

        # location related
        self.pager_text.x = 0
        self.pager_text.y = WIN_HEIGHT // 2
        self.pager_text.anchor_y = "top"

    def add_register_view(self):
        """Add a view to display registers."""
        mem_strings: List[str] = []
        # get flags
        flags = self.cpu.flags
        flag_array: str = [
            flags.N,
            flags.V,
            flags.U,
            flags.B,
            flags.D,
            flags.I,
            flags.Z,
            flags.C,
        ]
        flag_names: str = "N V U B D I Z C"
        mem_strings.append("STATUS: " + flag_names)
        mem_strings.append(
            "        " + " ".join(["x" if x else " " for x in flag_array])
        )

        # get program counter
        mem_strings.append(
            "PC: $" + f"{self.cpu.pc:0{4}X}" + f"    CYCLE: {self.cpu.cycle}"
        )
        # get registers
        mem_strings.append("A: $" + f"{self.cpu.a:0{2}X}    [{self.cpu.a}]")
        mem_strings.append("X: $" + f"{self.cpu.x:0{2}X}    [{self.cpu.x}]")
        mem_strings.append("Y: $" + f"{self.cpu.y:0{2}X}    [{self.cpu.y}]")
        # get stack pointer
        mem_strings.append(
            f"STKP: ${self.cpu.stkp:0{4}X}  REL: ${self.cpu.addr_rel:0{4}X}"
        )

        # add them into views
        mem_str: str = "\u2028".join(mem_strings)
        document = pyglet.text.document.FormattedDocument(mem_str)
        document.set_style(
            0,
            len(mem_str),
            dict(color=(255, 255, 255, 255), font_name="Perfect DOS VGA 437"),
        )
        self.status_text = pyglet.text.layout.TextLayout(
            document, multiline=True, wrap_lines=False, batch=self.batch
        )
        # location
        self.status_text.x = RIGHT_X
        self.status_text.y = WIN_HEIGHT
        self.status_text.anchor_y = "top"

    def add_disassembler_view(self):
        """Add a disassembler view."""
        disassembled: Dict[int, str] = self.cpu.disassemble(
            start=self.cpu.pc - DISBLR_BEFOR, end=self.cpu.pc + DISBLR_AFTER
        )
        _lines: List[str] = list(disassembled.values())
        # add an manual break to highlight current pc address

        mem_str: str = "\u2028".join(_lines)
        document = pyglet.text.document.FormattedDocument(mem_str)
        document.set_style(
            0,
            len(mem_str),
            dict(color=(255, 255, 255, 255), font_name="Perfect DOS VGA 437"),
        )
        self.dsblr_text = pyglet.text.layout.TextLayout(
            document, multiline=True, wrap_lines=False, batch=self.batch
        )

        # location related
        self.dsblr_text.x = RIGHT_X
        self.dsblr_text.y = DSBLR_HEIGHT
        self.dsblr_text.anchor_y = "top"

    def add_info_view(self):
        """Add a view for displaying debugger usage."""
        lines: str = (
            """== C: STEP == R: RESET == I: INTERRUPT == N: NMI == D: EXIT =="""
        )
        # add an manual break to highlight current pc address

        # mem_str: str = "\u2028".join()
        document = pyglet.text.document.FormattedDocument(lines)
        document.set_style(
            0,
            len(lines),
            dict(color=(255, 255, 255, 255), font_name="Perfect DOS VGA 437"),
        )
        self.info_text = pyglet.text.layout.TextLayout(
            document, multiline=True, wrap_lines=False, batch=self.batch
        )

        # location related
        self.info_text.x = WIN_WIDTH // 2
        self.info_text.y = WIN_HEIGHT * 0.055
        self.info_text.anchor_x = "center"
        self.info_text.anchor_y = "top"

    def load_debugging_program(self):
        """
        Load Program (assembled at https://www.masswerk.at/6502/assembler.html)
        This program multiplies 10 by 3. The CPU does not support multiplication
        and therefore will call/test multiple functions.

        Object code:
        *=$8000
        LDX #10
        STX $0000
        LDX #3
        STX $0001
        LDY $0000
        LDA #0
        CLC
        loop
        ADC $0001
        DEY
        BNE loop
        STA $0002
        NOP
        NOP
        NOP

        which converts to the magic string.
        """
        # offset to inject code
        offset: int = 0x1000
        self.dbg_start = offset

        for code in (
            "A2 0A 8E 00 00 A2 03 8E " +
            "01 00 AC 00 00 A9 00 18 " +
            "6D 01 00 88 D0 FA 8D 02 " +
            "00 EA EA EA EA EA EA EA " +
            "EA" 
        ).split(" "):
            self.cpu.bus.cpu_ram[offset] = eval("0x" + code)
            offset += 1

        # set memory to this address when reset
        self.cpu.bus.cpu_ram[0xFFFC] =  0x00
        self.cpu.bus.cpu_ram[0xFFFD] = 0x10

        self.cpu.reset()
