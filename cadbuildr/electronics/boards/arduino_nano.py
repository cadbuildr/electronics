"""A stylised Arduino Nano, assembled from the component library.

The Nano is the compact (18 x 45 mm) ATmega328 board with two 1x15 0.1" header
rows down the long edges, a mini-USB at the top, the MCU in a TQFP in the centre
and the usual reset button + indicator LEDs.
"""

from __future__ import annotations

from ..pcb import PCB
from ..components import (
    CeramicCapacitor,
    Crystal,
    LED,
    PinHeader,
    QFP,
    TactileButton,
    USBMicroB,
)

# Real Nano outline.
WIDTH = 18.0
HEIGHT = 45.0

_HW = WIDTH / 2.0   # 9.0
_HH = HEIGHT / 2.0  # 22.5


class ArduinoNano(PCB):
    """A Nano-class board populated from the PCB component library."""

    def __init__(self):
        super().__init__(WIDTH, HEIGHT, color="blue", name="ArduinoNano")

        # --- mini-USB at the top edge (pads kept on-board) ---
        self.place(USBMicroB(), ref="J-USB", x=0.0, y=19.5, rotation=0)

        # --- the ATmega328 (TQFP-32) in the centre ---
        self.place(QFP(32, body=7.0), ref="U1", x=0.0, y=0.0)

        # --- clock crystal beside the MCU ---
        self.place(Crystal("16MHz"), ref="Y1", x=0.0, y=-9.0, rotation=90)

        # --- the two 1x15 header rows down the long edges ---
        self.place(PinHeader(positions=15), ref="J1", x=-7.5, y=-0.5, rotation=90)
        self.place(PinHeader(positions=15), ref="J2", x=7.5, y=-0.5, rotation=90)

        # --- reset button + power/TX/RX indicator LEDs (LEDs dropped clear of
        #     the reset button body) ---
        self.place(TactileButton(), ref="SW-RST", x=0.0, y=14.0)
        self.place(LED("green", diameter=3.0), ref="D-PWR", x=-3.5, y=8.0)
        self.place(LED("yellow", diameter=3.0), ref="D-L", x=3.5, y=8.0)

        # --- a couple of decoupling caps (dropped clear of the crystal) ---
        self.place(CeramicCapacitor("100n"), ref="C1", x=-3.5, y=-16.5)
        self.place(CeramicCapacitor("100n"), ref="C2", x=3.5, y=-16.5)


__all__ = ["ArduinoNano"]
