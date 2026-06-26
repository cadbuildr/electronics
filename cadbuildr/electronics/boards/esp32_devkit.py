"""A stylised ESP32 DevKitC, assembled from the component library.

The DevKitC is the ~28 x 52 mm dev board carrying the ESP-WROOM-32 module (the
big shielded can in the top half), a micro-USB + USB-serial bridge at the bottom,
EN and BOOT buttons flanking the USB, and two 1x19 0.1" header rows down the long
edges.
"""

from __future__ import annotations

from ..pcb import PCB
from ..components import (
    CeramicCapacitor,
    LED,
    PinHeader,
    QFP,
    SOIC,
    TactileButton,
    USBMicroB,
)

# DevKitC outline.
WIDTH = 28.0
HEIGHT = 52.0

_HW = WIDTH / 2.0   # 14.0
_HH = HEIGHT / 2.0  # 26.0


class ESP32DevKit(PCB):
    """An ESP32-DevKitC-class board populated from the PCB component library."""

    def __init__(self):
        super().__init__(WIDTH, HEIGHT, color="black", name="ESP32DevKit")

        # --- ESP-WROOM-32 module (big shielded can) in the top half ---
        # Approximated with a large QFP body; the real module is a metal can.
        self.place(QFP(48, body=18.0), ref="U1", x=0.0, y=11.0)

        # --- micro-USB at the bottom edge ---
        self.place(USBMicroB(), ref="J-USB", x=0.0, y=-23.0, rotation=180)

        # --- EN / BOOT buttons flanking the USB (inboard of the 1x19 headers
        #     at x=±12.5 so the bodies stay clear) ---
        self.place(TactileButton(), ref="SW-EN", x=-7.5, y=-19.0)
        self.place(TactileButton(), ref="SW-BOOT", x=7.5, y=-19.0)

        # --- USB-to-serial bridge (SOIC) + 3V3 LDO ---
        self.place(SOIC(8), ref="U2", x=0.0, y=-14.0)
        self.place(SOIC(8), ref="U3", x=0.0, y=-7.0)

        # --- the two 1x19 header rows down the long edges ---
        self.place(PinHeader(positions=19), ref="J1", x=-12.5, y=-0.5, rotation=90)
        self.place(PinHeader(positions=19), ref="J2", x=12.5, y=-0.5, rotation=90)

        # --- power LED + decoupling caps ---
        self.place(LED("red", diameter=3.0), ref="D1", x=-9.0, y=-13.0)
        self.place(CeramicCapacitor("100n"), ref="C1", x=-6.0, y=-2.0)
        self.place(CeramicCapacitor("100n"), ref="C2", x=6.0, y=-2.0)


__all__ = ["ESP32DevKit"]
