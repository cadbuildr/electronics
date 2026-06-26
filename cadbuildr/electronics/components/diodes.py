"""Diodes and LEDs."""

from __future__ import annotations

from ..constants import COLORS, LED_COLOR_CHOICES, PITCH_100
from .._solids import add_cylinder_z, add_cylinder_x, add_lead_z
from ..footprint import ElectronicComponent, Footprint, two_pad


class LED(ElectronicComponent):
    """Through-hole LED — a coloured dome on a flanged base with two legs.

    ``diameter`` is the standard 3 mm or 5 mm package. The anode/cathode legs
    drop into a two-pad footprint at 0.1" pitch."""

    def __init__(self, color: str = "red", diameter: float = 5.0, lead_spacing: float = PITCH_100):
        super().__init__()
        self.color_name = color
        self.diameter = diameter
        self.lead_spacing = lead_spacing
        hexc = LED_COLOR_CHOICES.get(color, color)

        r = diameter / 2.0
        # Flange at the base.
        add_cylinder_z(self, r + 0.3, 1.0, z0=0.0)
        # Main cylindrical body + a (approximate) domed top.
        add_cylinder_z(self, r, diameter * 0.8, z0=1.0)
        add_cylinder_z(self, r * 0.7, diameter * 0.25, z0=1.0 + diameter * 0.8)
        self.paint(hexc)

        for sx in (-1, 1):
            add_lead_z(self, sx * lead_spacing / 2.0, 0.0, radius=0.25, depth=3.0)

    def footprint(self) -> Footprint:
        return Footprint(
            name="LED_THT",
            pads=two_pad(self.lead_spacing, drill=0.8),
            courtyard=(self.diameter + 1.0, self.diameter + 1.0),
        )


class Diode(ElectronicComponent):
    """Axial signal/rectifier diode (DO-35 / DO-41 style black cylinder)."""

    def __init__(self, part_number: str = "1N4148", lead_spacing: float = 0.4 * 25.4):
        super().__init__()
        self.part_number = part_number
        self.lead_spacing = lead_spacing
        body_r = 0.95
        self._axis_z = body_r + 0.5
        add_cylinder_x(self, body_r, lead_spacing - 4.0, cz=self._axis_z)
        # Cathode band (cosmetic); body colour painted last so it dominates.
        add_cylinder_x(
            self, body_r + 0.05, 0.6, cz=self._axis_z, x0=(lead_spacing - 4.0) / 2.0 - 1.2
        )
        self.paint(COLORS.plastic_black)
        for sx in (-1, 1):
            add_lead_z(self, sx * lead_spacing / 2.0, 0.0, radius=0.22, depth=3.0)

    def footprint(self) -> Footprint:
        return Footprint(
            name="D_AXIAL",
            pads=two_pad(self.lead_spacing, drill=0.8),
            courtyard=(self.lead_spacing + 2.0, 2.5),
        )


__all__ = ["LED", "Diode"]
