"""A stylised Raspberry-Pi-style single-board computer, assembled from the
component library.

Like :mod:`arduino_uno`, this is a recognisable approximation rather than a
pin-accurate clone: the 40-pin GPIO header runs along the top edge, the SoC is
a big QFP in the middle, and the bulky I/O (USB stack + Ethernet) sits on the
right edge where it does on a real Pi.

The outline is the real Pi Model B footprint — 85 x 56 mm with the
characteristic 3 mm rounded corners (approximated here as 3 mm chamfers) and the
58 x 49 mm mounting-hole rectangle.
"""

from __future__ import annotations

from ..pcb import PCB
from ..components import (
    CeramicCapacitor,
    LED,
    PinHeader,
    QFP,
    RJ45,
    USBTypeA,
)

# Real Pi Model B outline.
WIDTH = 85.0
HEIGHT = 56.0

_HW = WIDTH / 2.0   # 42.5
_HH = HEIGHT / 2.0  # 28.0
_CHAMFER = 3.0      # real Pi has 3 mm corner radius; chamfer is a close stand-in

# 8-vertex chamfered rectangle (rounded-corner stand-in), centred, +Y up.
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


class RaspberryPi(PCB):
    """A Pi-class SBC populated from the PCB component library."""

    def __init__(self):
        super().__init__(
            WIDTH, HEIGHT, color="green", name="RaspberryPi", outline=_OUTLINE
        )

        # --- 40-pin GPIO header along the top edge ---
        self.place(PinHeader(positions=20, rows=2), ref="J8", x=-3.5, y=23.5)

        # --- the SoC (big QFP/BGA stand-in) near board centre ---
        self.place(QFP(64), ref="U1", x=-7.0, y=0.0)

        # --- right-edge I/O: stacked USB + Ethernet ---
        self.place(USBTypeA(), ref="J-USB1", x=33.0, y=14.0, rotation=90)
        self.place(USBTypeA(), ref="J-USB2", x=33.0, y=-2.0, rotation=90)
        self.place(RJ45(), ref="J-ETH", x=32.0, y=-18.0, rotation=90)

        # --- power + activity LEDs (corner near the GPIO/microSD edge) ---
        # 3 mm packages spaced 4 mm apart (flange dia 3.6 mm) so they clear.
        self.place(LED("red", diameter=3.0), ref="D-PWR", x=-39.0, y=20.0)
        self.place(LED("green", diameter=3.0), ref="D-ACT", x=-35.0, y=20.0)

        # --- a scattering of decoupling caps around the SoC ---
        for i, (dx, dy) in enumerate([(-20, 8), (-4, 8), (-20, -8), (-4, -8)]):
            self.place(CeramicCapacitor("100n"), ref=f"C{i + 1}", x=dx, y=dy)

        # --- mounting holes (genuine 58 x 49 mm Pi rectangle) ---
        self.mounting_hole(-39.0, 24.5)
        self.mounting_hole(19.0, 24.5)
        self.mounting_hole(-39.0, -24.5)
        self.mounting_hole(19.0, -24.5)


__all__ = ["RaspberryPi"]
