"""Main execution script."""

import pyglet

from pathlib import Path

from nsim.hw.cpu import SY6502
from nsim.hw.bus import Bus6502
from nsim.interface.debugger import Debugger


def main():
    # debugging from video 2
    nes: Bus6502 = Bus6502(cartridge_path="nestest.nes")
    debugger: Debugger = Debugger(nes=nes)
    pyglet.app.run()


if __name__ == "__main__":
    main()
