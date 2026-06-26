"""Integrated circuits: DIP (through-hole) and SOIC/QFP (surface mount)."""

from __future__ import annotations

from ..constants import COLORS, DIP_ROW_SPACING, PITCH_100
from .._solids import add_box, add_cylinder_z, add_pin_z
from ..footprint import ElectronicComponent, Footprint, Pad


class DIP(ElectronicComponent):
    """Dual-in-line package IC (e.g. ATmega328, 555, logic chips).

    ``pins`` is the total pin count (even). Pins run in two rows
    ``row_spacing`` apart on a 0.1" pitch."""

    def __init__(
        self,
        pins: int = 28,
        row_spacing: float = DIP_ROW_SPACING,
        pitch: float = PITCH_100,
        label: str = "DIP",
    ):
        super().__init__()
        if pins % 2 != 0:
            raise ValueError("DIP pin count must be even")
        self.pins = pins
        self.row_spacing = row_spacing
        self.pitch = pitch
        self.label = label
        per_row = pins // 2

        # Black body.
        body_len = per_row * pitch
        add_box(self, body_len, row_spacing - 1.5, 3.5, z0=0.5)
        self.paint(COLORS.ic_black)
        # Orientation notch.
        add_cylinder_z(self, 0.9, 0.6, cx=-body_len / 2.0 + 0.9, cy=0.0, z0=3.4)
        self.paint(COLORS.plastic_black)

        # Build pads + matching legs.
        self._pads: list[Pad] = []
        x0 = -(per_row - 1) * pitch / 2.0
        n = 1
        # Bottom row (left→right), then top row (right→left) — DIP numbering.
        for c in range(per_row):
            self._pads.append(
                Pad(x0 + c * pitch, -row_spacing / 2.0, drill=0.8, pad_diameter=1.6, name=str(n))
            )
            n += 1
        for c in range(per_row - 1, -1, -1):
            self._pads.append(
                Pad(x0 + c * pitch, row_spacing / 2.0, drill=0.8, pad_diameter=1.6, name=str(n))
            )
            n += 1
        for pad in self._pads:
            add_pin_z(self, pad.x, pad.y, 0.5, top=0.8, bottom=-3.2)
        # Single colour per Part; the black body dominates over the legs.
        self.paint(COLORS.ic_black)

    def footprint(self) -> Footprint:
        return Footprint(
            name=f"DIP-{self.pins}",
            pads=self._pads,
            courtyard=(self.pins // 2 * self.pitch + 1.0, self.row_spacing + 2.0),
        )


class SOIC(ElectronicComponent):
    """Small-outline IC (gull-wing SMD). No drills — copper lands only."""

    def __init__(self, pins: int = 8, pitch: float = 1.27, body_width: float = 3.9):
        super().__init__()
        if pins % 2 != 0:
            raise ValueError("SOIC pin count must be even")
        self.pins = pins
        self.pitch = pitch
        self.body_width = body_width
        per_row = pins // 2
        body_len = per_row * pitch + 0.6

        add_box(self, body_len, body_width, 1.5, z0=0.1)
        self.paint(COLORS.ic_black)
        add_cylinder_z(self, 0.4, 0.3, cx=-body_len / 2.0 + 0.7, cy=body_width / 2.0 - 0.7, z0=1.4)
        self.paint(COLORS.plastic_black)

        land_y = body_width / 2.0 + 0.5
        x0 = -(per_row - 1) * pitch / 2.0
        self._pads: list[Pad] = []
        n = 1
        for c in range(per_row):
            self._pads.append(Pad(x0 + c * pitch, -land_y, drill=0.0, pad_diameter=0.6, name=str(n)))
            n += 1
        for c in range(per_row - 1, -1, -1):
            self._pads.append(Pad(x0 + c * pitch, land_y, drill=0.0, pad_diameter=0.6, name=str(n)))
            n += 1

    def footprint(self) -> Footprint:
        return Footprint(
            name=f"SOIC-{self.pins}",
            pads=self._pads,
            courtyard=(self.pins // 2 * self.pitch + 1.0, self.body_width + 2.0),
        )


class QFP(ElectronicComponent):
    """Quad flat package (SMD, pins on all four sides)."""

    def __init__(self, pins: int = 32, pitch: float = 0.8, body: float = 7.0):
        super().__init__()
        if pins % 4 != 0:
            raise ValueError("QFP pin count must be divisible by 4")
        self.pins = pins
        self.pitch = pitch
        self.body = body
        per_side = pins // 4

        add_box(self, body, body, 1.4, z0=0.1)
        self.paint(COLORS.ic_black)
        add_cylinder_z(self, 0.5, 0.3, cx=-body / 2.0 + 1.2, cy=-body / 2.0 + 1.2, z0=1.4)
        self.paint(COLORS.plastic_black)

        land = body / 2.0 + 0.6
        x0 = -(per_side - 1) * pitch / 2.0
        self._pads: list[Pad] = []
        n = 1
        for c in range(per_side):  # bottom
            self._pads.append(Pad(x0 + c * pitch, -land, drill=0.0, pad_diameter=0.45, name=str(n))); n += 1
        for c in range(per_side):  # right
            self._pads.append(Pad(land, x0 + c * pitch, drill=0.0, pad_diameter=0.45, name=str(n))); n += 1
        for c in range(per_side - 1, -1, -1):  # top
            self._pads.append(Pad(x0 + c * pitch, land, drill=0.0, pad_diameter=0.45, name=str(n))); n += 1
        for c in range(per_side - 1, -1, -1):  # left
            self._pads.append(Pad(-land, x0 + c * pitch, drill=0.0, pad_diameter=0.45, name=str(n))); n += 1

    def footprint(self) -> Footprint:
        return Footprint(name=f"QFP-{self.pins}", pads=self._pads, courtyard=(self.body + 3.0, self.body + 3.0))


__all__ = ["DIP", "SOIC", "QFP"]
