"""Miscellaneous parts: crystals, tactile buttons."""

from __future__ import annotations

from ..constants import COLORS
from .._solids import add_box, add_cylinder_x, add_lead_z, add_pin_z
from ..footprint import ElectronicComponent, Footprint, Pad, two_pad


class Crystal(ElectronicComponent):
    """HC-49 quartz crystal — a low metal can lying on its side."""

    def __init__(self, frequency: str = "16MHz", lead_spacing: float = 4.88):
        super().__init__()
        self.frequency = frequency
        self.lead_spacing = lead_spacing
        axis_z = 2.2
        add_cylinder_x(self, 2.0, 11.0, cz=axis_z)
        # Flatten the can a touch with a top plate for the classic HC-49 look.
        add_box(self, 11.0, 4.5, 0.6, z0=axis_z + 1.6)
        self.paint(COLORS.metal_shell)
        for sx in (-1, 1):
            add_lead_z(self, sx * lead_spacing / 2.0, 0.0, radius=0.25, depth=3.0)

    def footprint(self) -> Footprint:
        return Footprint(
            name="HC49",
            pads=two_pad(self.lead_spacing, drill=0.8),
            courtyard=(13.0, 5.5),
        )


class TactileButton(ElectronicComponent):
    """6 mm through-hole tactile push button (4 legs)."""

    def __init__(self):
        super().__init__()
        from .._solids import add_cylinder_z

        # Actuator (cosmetic) then the black housing painted last so it wins.
        add_cylinder_z(self, 1.7, 1.5, z0=3.5)
        add_box(self, 6.0, 6.0, 3.5, z0=0.0)
        self.paint(COLORS.plastic_black)

        self._pads = [
            Pad(-3.25, -2.25, drill=1.0, pad_diameter=1.8, name="1"),
            Pad(3.25, -2.25, drill=1.0, pad_diameter=1.8, name="2"),
            Pad(-3.25, 2.25, drill=1.0, pad_diameter=1.8, name="3"),
            Pad(3.25, 2.25, drill=1.0, pad_diameter=1.8, name="4"),
        ]
        for pad in self._pads:
            add_pin_z(self, pad.x, pad.y, 0.5, top=0.0, bottom=-3.0)
        self.paint(COLORS.tin)

    def footprint(self) -> Footprint:
        return Footprint(name="SW_TACT_6MM", pads=self._pads, courtyard=(7.0, 7.0))


__all__ = ["Crystal", "TactileButton"]
