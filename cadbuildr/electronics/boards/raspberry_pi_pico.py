"""A stylised Raspberry Pi Pico, assembled from the component library.

The Pico is the small (21 x 51 mm) RP2040 board with castellated 0.1" headers
down both long edges, a micro-USB at the top, the RP2040 in the centre and the
BOOTSEL button just below the USB. The outline carries the Pico's 1 mm corner
chamfers.
"""

from __future__ import annotations

from ..pcb import PCB
from ..components import (
    CeramicCapacitor,
    LED,
    PinHeader,
    QFP,
    TactileButton,
    USBMicroB,
)

# Real Pico outline.
WIDTH = 21.0
HEIGHT = 51.0

_HW = WIDTH / 2.0   # 10.5
_HH = HEIGHT / 2.0  # 25.5
_CHAMFER = 1.0      # Pico has small ~1 mm corner chamfers

_OUTLINE = [
    (-_HW + _CHAMFER, -_HH),
    (_HW - _CHAMFER, -_HH),
    (_HW, -_HH + _CHAMFER),
    (_HW, _HH - _CHAMFER),
    (_HW - _CHAMFER, _HH),
    (-_HW + _CHAMFER, _HH),
    (-_HW, _HH - _CHAMFER),
    (-_HW, -_HH + _CHAMFER),
]


class RaspberryPiPico(PCB):
    """A Pico-class board populated from the PCB component library."""

    def __init__(self):
        super().__init__(
            WIDTH, HEIGHT, color="green", name="RaspberryPiPico", outline=_OUTLINE
        )

        # --- micro-USB at the top edge ---
        self.place(USBMicroB(), ref="J-USB", x=0.0, y=24.0, rotation=0)

        # --- BOOTSEL button just below the USB ---
        self.place(TactileButton(), ref="SW-BOOT", x=0.0, y=17.0)

        # --- the RP2040 in the middle (QFN stand-in) ---
        self.place(QFP(56, body=7.0), ref="U1", x=0.0, y=2.0)

        # --- the two castellated 0.1" headers down the long edges. Real Pico
        #     column spacing is 17.78 mm (0.7"), i.e. x=±8.89; centred in Y so
        #     the 50.8 mm rows stay on the 51 mm board. ---
        self.place(PinHeader(positions=20), ref="J1", x=-8.89, y=0.0, rotation=90)
        self.place(PinHeader(positions=20), ref="J2", x=8.89, y=0.0, rotation=90)

        # --- on-board LED (near the RP2040, top-left) + decoupling caps ---
        self.place(LED("green", diameter=3.0), ref="D1", x=-4.0, y=8.0)
        self.place(CeramicCapacitor("100n"), ref="C1", x=-4.0, y=-5.0)
        self.place(CeramicCapacitor("100n"), ref="C2", x=4.0, y=-5.0)


__all__ = ["RaspberryPiPico"]
