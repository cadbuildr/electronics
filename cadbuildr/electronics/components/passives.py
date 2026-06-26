"""Passive components: resistors and capacitors (through-hole and SMD)."""

from __future__ import annotations

from typing import ClassVar

from ..constants import COLORS, PITCH_100
from .._solids import add_box, add_cylinder_z, add_cylinder_x, add_lead_z
from ..footprint import ElectronicComponent, Footprint, Pad, two_pad


class Resistor(ElectronicComponent):
    """Axial through-hole resistor (the classic banded cylinder on two legs).

    ``lead_spacing`` is the hole-to-hole pitch (0.4" by default for a 1/4 W
    part). ``resistance`` is carried for the BOM / silkscreen only.
    """

    def __init__(
        self,
        resistance: str = "1k",
        lead_spacing: float = 0.4 * 25.4,
        body_length: float = 6.3,
        body_radius: float = 1.15,
        color: str = COLORS.resistor_beige,
    ):
        super().__init__()
        self.resistance = resistance
        self.lead_spacing = lead_spacing
        self.body_length = min(body_length, lead_spacing - 2.0)
        self.body_radius = body_radius
        self._axis_z = body_radius + 0.6  # lift the body off the board

        # Body — a horizontal cylinder along X.
        add_cylinder_x(self, body_radius, self.body_length, cz=self._axis_z)
        self.paint(color)

        # Two leads dropping into the board at the hole positions.
        for sx in (-1, 1):
            add_lead_z(self, sx * lead_spacing / 2.0, 0.0, radius=0.25, depth=3.0)

    def footprint(self) -> Footprint:
        return Footprint(
            name="R_AXIAL",
            pads=two_pad(self.lead_spacing, drill=0.8),
            courtyard=(self.lead_spacing + 2.0, 2 * self.body_radius + 1.0),
        )


class ResistorSMD(ElectronicComponent):
    """Surface-mount chip resistor (0805 by default). No board holes — the
    footprint is pure copper land, demonstrating the SMD path."""

    SIZES: ClassVar[dict[str, tuple]] = {
        # imperial code: (length, width, height, pad pitch, pad size)
        "0603": (1.6, 0.8, 0.45, 1.5, 0.8),
        "0805": (2.0, 1.25, 0.5, 1.9, 1.0),
        "1206": (3.2, 1.6, 0.55, 3.0, 1.2),
    }

    def __init__(self, resistance: str = "10k", size: str = "0805"):
        super().__init__()
        if size not in self.SIZES:
            raise ValueError(f"Unknown chip size {size!r}; pick {list(self.SIZES)}")
        self.resistance = resistance
        self.size = size
        length, width, height, self._pitch, self._pad = self.SIZES[size]
        self._length = length

        add_box(self, length, width, height, z0=0.0)
        # Metallised end caps (cosmetic). The kernel paints a Part a single
        # colour, so the final paint() below sets the dominant body colour.
        for sx in (-1, 1):
            add_box(self, length * 0.18, width, height, cx=sx * length * 0.41, z0=0.0)
        self.paint(COLORS.ic_black)

    def footprint(self) -> Footprint:
        return Footprint(
            name=f"R_{self.size}",
            pads=[
                Pad(-self._pitch / 2, 0.0, drill=0.0, pad_diameter=self._pad, name="1"),
                Pad(self._pitch / 2, 0.0, drill=0.0, pad_diameter=self._pad, name="2"),
            ],
            courtyard=(self._length + 1.0, 1.6),
        )


class CeramicCapacitor(ElectronicComponent):
    """Radial ceramic disc / MLCC capacitor on two legs."""

    def __init__(self, value: str = "100n", lead_spacing: float = PITCH_100):
        super().__init__()
        self.value = value
        self.lead_spacing = lead_spacing
        z0 = 2.0
        add_box(self, 4.0, 1.6, 4.5, z0=z0)
        self.paint(COLORS.ceramic_tan)
        for sx in (-1, 1):
            add_lead_z(self, sx * lead_spacing / 2.0, 0.0, radius=0.22, depth=3.0)

    def footprint(self) -> Footprint:
        return Footprint(
            name="C_DISC",
            pads=two_pad(self.lead_spacing, drill=0.7),
            courtyard=(self.lead_spacing + 2.0, 2.0),
        )


class ElectrolyticCapacitor(ElectronicComponent):
    """Radial aluminium electrolytic capacitor (the cylindrical can)."""

    def __init__(
        self,
        value: str = "100u",
        diameter: float = 6.3,
        height: float = 11.0,
        lead_spacing: float = 2.5,
        color: str = COLORS.plastic_blue,
    ):
        super().__init__()
        self.value = value
        self.diameter = diameter
        self.height = height
        self.lead_spacing = lead_spacing
        base_z = 0.8
        # Crimped base disc (darker) then the can; final paint() wins for the
        # whole Part, so paint the can colour last.
        add_cylinder_z(self, diameter / 2.0 + 0.1, base_z, z0=0.0)
        add_cylinder_z(self, diameter / 2.0, height, z0=base_z)
        self.paint(color)
        for sx in (-1, 1):
            add_lead_z(self, sx * lead_spacing / 2.0, 0.0, radius=0.3, depth=3.0)

    def footprint(self) -> Footprint:
        return Footprint(
            name="CP_RADIAL",
            pads=two_pad(self.lead_spacing, drill=0.9),
            courtyard=(self.diameter + 1.0, self.diameter + 1.0),
        )


__all__ = [
    "Resistor",
    "ResistorSMD",
    "CeramicCapacitor",
    "ElectrolyticCapacitor",
]
