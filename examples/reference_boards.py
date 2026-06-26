"""Render the reference boards used to validate the library.

    python examples/reference_boards.py            # Arduino Uno
    python examples/reference_boards.py raspberry   # Raspberry Pi
"""

import sys

from cadbuildr.foundation import show

from cadbuildr.electronics.boards import ArduinoUno, RaspberryPi


if __name__ == "__main__":
    which = sys.argv[1] if len(sys.argv) > 1 else "arduino"
    board = RaspberryPi() if which.startswith("ras") else ArduinoUno()
    print(f"{type(board).__name__}: {len(board.placements)} components")
    show(board)
