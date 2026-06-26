"""Connectors: pin headers, USB, RJ45 Ethernet, barrel jack, screw terminals."""

from __future__ import annotations

from ..constants import COLORS, PITCH_100
from .._solids import add_box, add_cylinder_x, add_cylinder_z, add_pin_z
from ..footprint import (
    ElectronicComponent,
    Footprint,
    Pad,
    grid_pads,
)


class PinHeader(ElectronicComponent):
    """Male pin header, ``rows`` × ``positions`` on a 2.54 mm grid."""

    def __init__(self, positions: int = 8, rows: int = 1, pitch: float = PITCH_100):
        super().__init__()
        if positions < 1 or rows < 1:
            raise ValueError("positions and rows must be >= 1")
        self.positions = positions
        self.rows = rows
        self.pitch = pitch
        self._pads = grid_pads(rows, positions, pitch, pitch, drill=1.0, pad_diameter=1.8)

        base_w = positions * pitch
        base_d = rows * pitch
        add_box(self, base_w, base_d, 2.5, z0=0.0)
        self.paint(COLORS.plastic_black)
        # Square posts coincident with the pads.
        for pad in self._pads:
            add_pin_z(self, pad.x, pad.y, 0.64, top=6.0, bottom=-3.0)
        self.paint(COLORS.gold)

    def footprint(self) -> Footprint:
        return Footprint(
            name=f"PINHDR_{self.rows}x{self.positions}",
            pads=self._pads,
            courtyard=(self.positions * self.pitch, self.rows * self.pitch),
        )


class ScrewTerminal(ElectronicComponent):
    """Rising-cage screw terminal block (5.08 mm pitch)."""

    def __init__(self, positions: int = 2, pitch: float = 5.08):
        super().__init__()
        self.positions = positions
        self.pitch = pitch
        self._pads = grid_pads(1, positions, pitch, pitch, drill=1.2, pad_diameter=2.4)

        width = positions * pitch
        add_box(self, width, 8.0, 9.5, z0=0.0)
        # Screw heads (cosmetic); body colour painted last so it dominates.
        for pad in self._pads:
            add_cylinder_z(self, 1.4, 1.0, cx=pad.x, cy=2.5, z0=8.5)
        self.paint(COLORS.plastic_blue)

    def footprint(self) -> Footprint:
        return Footprint(
            name=f"SCREWTERM_{self.positions}",
            pads=self._pads,
            courtyard=(self.positions * self.pitch + 1.0, 9.0),
        )


class USBTypeA(ElectronicComponent):
    """Through-hole USB Type-A host receptacle (the metal box)."""

    def __init__(self):
        super().__init__()
        # Metal shell.
        add_box(self, 14.5, 13.0, 6.5, z0=0.0)
        self.paint(COLORS.metal_shell)
        # Dark plastic insert visible at the mouth.
        add_box(self, 11.5, 2.0, 4.0, cy=-5.0, z0=1.2)
        self.paint(COLORS.plastic_black)

        # 4 signal pins in a row + 2 board-lock through-holes.
        self._pads = [
            Pad(-3.5 + i * 2.0, 4.0, drill=0.9, pad_diameter=1.6, name=str(i + 1))
            for i in range(4)
        ]
        self._pads += [
            Pad(-6.5, 4.5, drill=2.3, pad_diameter=3.0, name="SH1"),
            Pad(6.5, 4.5, drill=2.3, pad_diameter=3.0, name="SH2"),
        ]
        for pad in self._pads:
            add_cylinder_z(self, 0.35, 6.0, cx=pad.x, cy=pad.y, z0=-3.0)
        self.paint(COLORS.tin)

    def footprint(self) -> Footprint:
        return Footprint(name="USB_A_TH", pads=self._pads, courtyard=(15.0, 14.0))


class USBMicroB(ElectronicComponent):
    """USB Micro-B receptacle — 5 SMD signal pads + 2 through-hole shield tabs."""

    def __init__(self):
        super().__init__()
        add_box(self, 6.5, 1.5, 1.6, cy=-2.0, z0=0.4)
        add_box(self, 7.5, 5.0, 2.5, z0=0.0)
        self.paint(COLORS.metal_shell)

        self._pads = [
            Pad(-1.3 + i * 0.65, 3.0, drill=0.0, pad_diameter=0.45, name=str(i + 1))
            for i in range(5)
        ]
        self._pads += [
            Pad(-3.4, 1.0, drill=1.0, pad_diameter=1.8, name="SH1"),
            Pad(3.4, 1.0, drill=1.0, pad_diameter=1.8, name="SH2"),
        ]

    def footprint(self) -> Footprint:
        return Footprint(name="USB_MICRO_B", pads=self._pads, courtyard=(8.0, 6.0))


class RJ45(ElectronicComponent):
    """RJ45 (8P8C) Ethernet jack — large shielded box with 8 pins."""

    def __init__(self):
        super().__init__()
        add_box(self, 16.0, 21.0, 13.5, z0=0.0)
        self.paint(COLORS.metal_shell)
        # Cable mouth.
        add_box(self, 12.0, 3.0, 9.0, cy=-9.5, z0=2.0)
        self.paint(COLORS.plastic_black)

        # 8 signal pins (two staggered rows) + 2 shield mounting posts.
        self._pads = []
        for i in range(8):
            row = i % 2
            self._pads.append(
                Pad(-4.45 + i * 1.27, 6.0 + row * 2.54, drill=0.9, pad_diameter=1.6, name=str(i + 1))
            )
        self._pads += [
            Pad(-7.0, 8.0, drill=3.2, pad_diameter=4.0, name="SH1"),
            Pad(7.0, 8.0, drill=3.2, pad_diameter=4.0, name="SH2"),
        ]
        for pad in self._pads:
            add_cylinder_z(self, 0.35, 3.0, cx=pad.x, cy=pad.y, z0=-3.0)
        self.paint(COLORS.tin)

    def footprint(self) -> Footprint:
        return Footprint(name="RJ45", pads=self._pads, courtyard=(17.0, 22.0))


class BarrelJack(ElectronicComponent):
    """DC barrel power jack (2.1 mm) — black body with a horizontal barrel."""

    def __init__(self):
        super().__init__()
        # The protruding barrel (cosmetic) + pins, then the body colour last
        # so the black housing dominates the single-colour Part.
        add_cylinder_z(self, 3.5, 2.0, cy=-7.5, z0=4.0)
        self._pads = [
            Pad(-3.5, 4.0, drill=1.5, pad_diameter=2.6, name="TIP"),
            Pad(3.5, 4.0, drill=1.5, pad_diameter=2.6, name="SLEEVE"),
            Pad(0.0, -2.0, drill=1.5, pad_diameter=2.6, name="SW"),
        ]
        for pad in self._pads:
            add_cylinder_z(self, 0.5, 5.0, cx=pad.x, cy=pad.y, z0=-3.0)
        add_box(self, 9.0, 14.0, 11.0, z0=0.0)
        self.paint(COLORS.plastic_black)

    def footprint(self) -> Footprint:
        return Footprint(name="BARREL_JACK", pads=self._pads, courtyard=(10.0, 15.0))


__all__ = [
    "PinHeader",
    "ScrewTerminal",
    "USBTypeA",
    "USBMicroB",
    "RJ45",
    "BarrelJack",
]
