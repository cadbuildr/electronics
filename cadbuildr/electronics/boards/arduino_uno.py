"""A stylised Arduino-Uno-style board, built entirely from the component
library to validate the framework end-to-end.

Coordinates are board-centred (origin at the centre of the 68.58 x 53.34 mm
outline) and approximate the real Uno layout closely enough to be recognisable
in the viewer: the USB and barrel jack hang off the left edge, the ATmega DIP
sits in the middle next to its crystal, and the four 0.1" header banks line the
top and bottom edges.

The board outline is the **genuine** Arduino Uno R3 edge-cut shape — the iconic
profile with the chamfered top-right corner and the right-edge notch where the
board steps in from 68.58 mm to 66.04 mm wide. The vertices were taken from the
official Arduino Uno R3 KiCad footprint (Edge.Cuts / silkscreen perimeter) and
re-centred / flipped to our Y-up, board-centred frame.
"""

from __future__ import annotations

from ..pcb import PCB
from ..components import (
    BarrelJack,
    CeramicCapacitor,
    Crystal,
    DIP,
    ElectrolyticCapacitor,
    LED,
    PinHeader,
    TactileButton,
    USBTypeA,
)

# Real Uno R3 outline — 68.58 mm x 53.34 mm.
WIDTH = 68.58
HEIGHT = 53.34

# Genuine Arduino Uno R3 perimeter, centred at the origin with +Y pointing up.
# Source: Arduino_Uno_R3 KiCad footprint board-edge (origin bottom-left, Y-down),
# transformed by x' = x - 34.29, y' = -y - 26.67. The notch + chamfer on the
# right edge (USB is on the *left*) is what makes the Uno instantly recognisable.
_OUTLINE = [
    (-34.29, -26.670),  # bottom-left
    (31.75, -26.670),  # bottom edge
    (31.75, -25.400),  # step up to the chamfer
    (34.29, -22.860),  # chamfer out to full width
    (34.29, 11.430),  # right edge (full-width lower section)
    (31.75, 13.970),  # chamfer in — the right-edge notch
    (31.75, 25.146),  # inset upper section
    (30.226, 26.670),  # chamfer at the top-right corner
    (-34.29, 26.670),  # top edge → top-left
]


class ArduinoUno(PCB):
    """An Uno-class board populated from the PCB component library."""

    def __init__(self):
        super().__init__(
            WIDTH, HEIGHT, color="blue", name="ArduinoUno", outline=_OUTLINE
        )

        # --- left-edge connectors (mouths overhang the board edge, as on the
        #     real Uno: USB-B above the barrel power jack) ---
        self.place(USBTypeA(), ref="J-USB", x=-28.0, y=14.0, rotation=-90)
        self.place(BarrelJack(), ref="J-PWR", x=-28.0, y=-14.0, rotation=-90)

        # --- the microcontroller + clock (ATmega long axis vertical, crystal
        #     seated right beside it, as on the real board) ---
        self.place(DIP(28), ref="U1", x=4.0, y=-2.0, rotation=90)
        self.place(Crystal("16MHz"), ref="Y1", x=-7.0, y=7.0, rotation=0)

        # --- the four header banks (digital top, power+analog bottom), spans
        #     matched to the real R3 0.1" rows ---
        self.place(PinHeader(positions=10), ref="J-D8-13", x=-6.0, y=24.13)
        self.place(PinHeader(positions=8), ref="J-D0-7", x=18.0, y=24.13)
        self.place(PinHeader(positions=8), ref="J-PWRHDR", x=2.0, y=-24.13)
        self.place(PinHeader(positions=6), ref="J-ANALOG", x=21.0, y=-24.13)

        # --- user IO + indicators (reset clear of the USB shell; ON/L LEDs
        #     beside the ATmega) ---
        self.place(TactileButton(), ref="SW-RST", x=-16.0, y=17.0)
        self.place(LED("green"), ref="D-ON", x=-4.0, y=14.0)
        self.place(LED("yellow"), ref="D-L", x=-10.0, y=14.0)

        # --- power filtering (electrolytics stacked apart, clear of the barrel) ---
        self.place(ElectrolyticCapacitor("47u"), ref="C1", x=-16.0, y=-9.0)
        self.place(ElectrolyticCapacitor("47u"), ref="C2", x=-16.0, y=1.0)
        self.place(CeramicCapacitor("100n"), ref="C3", x=-2.0, y=-12.0)

        # --- mounting holes (genuine Uno R3 positions, board-centred) ---
        # Official Uno hole centres (origin bottom-left): (15.24, 50.8),
        # (66.04, 35.56), (66.04, 7.62), (13.97, 2.54) → centred below.
        self.mounting_hole(-19.05, 24.13)
        self.mounting_hole(31.75, 8.89)
        self.mounting_hole(31.75, -19.05)
        self.mounting_hole(-20.32, -24.13)


__all__ = ["ArduinoUno"]
