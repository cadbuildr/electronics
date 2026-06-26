"""Minimal end-to-end example: a header, a resistor and an LED on a small board.

Run with the foundation viewer::

    python examples/blinky.py
"""

from cadbuildr.foundation import show

from cadbuildr.electronics import PCB, LED, PinHeader, Resistor


def build() -> PCB:
    pcb = PCB(50, 24, color="blue", name="Blinky")
    # One line per part — each call drills the board *and* seats the body.
    pcb.place(PinHeader(positions=2), ref="J1", x=-20, y=0)
    pcb.place(Resistor("220"), ref="R1", x=-2, y=0)
    pcb.place(LED("red"), ref="D1", x=18, y=0)
    return pcb


if __name__ == "__main__":
    show(build())
