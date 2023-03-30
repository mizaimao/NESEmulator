"""Main execution script."""

import pyglet

from nsim.hw.cpu import SY6502
from nsim.interface.debugger import Debugger



def main():

    cpu: SY6502 = SY6502()
    debugger: Debugger = Debugger(cpu=cpu)
    pyglet.app.run()


if __name__ == "__main__":
    main()
