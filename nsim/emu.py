"""Main execution script."""

import pyglet

from nsim.hw.cpu import SY6502
from nsim.hw.bus import Bus6502
from nsim.interface.debugger import Debugger


def main():
    # debugging from video 2
    nes: Bus6502 = Bus6502()
    debugger: Debugger = Debugger(cpu=nes.cpu)
    pyglet.app.run()


if __name__ == "__main__":
    main()
