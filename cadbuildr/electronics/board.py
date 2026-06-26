"""The bare PCB substrate as a foundation ``Part``.

The board is a flat FR-4 slab extruded from ``z = 0`` (bottom) to
``z = thickness`` (top copper). Footprint holes are *cut* operations added on
top of the base extrusion, so the board geometry always reflects every
component that has been placed on it.
"""

from __future__ import annotations

from cadbuildr.foundation import (
    Circle,
    Extrusion,
    Line,
    Part,
    Point,
    Polygon,
    Rectangle,
    Sketch,
)

from .constants import BOARD_COLOR_CHOICES, COLORS, DEFAULT_BOARD_THICKNESS
from .footprint import Footprint, Pad, paint_pads


class PCBBoard(Part):
    """A rectangular printed-circuit board.

    The origin sits at the board centre, in the board plane. Use
    :meth:`apply_footprint` to drill a placed footprint, or :meth:`drill` for a
    single mounting hole.
    """

    def __init__(
        self,
        width: float,
        height: float,
        thickness: float = DEFAULT_BOARD_THICKNESS,
        color: str = "green",
        corner_radius: float = 0.0,
        show_pads: bool = True,
        outline: list[tuple[float, float]] | None = None,
    ):
        super().__init__()
        self.width = width
        self.height = height
        self.thickness = thickness
        self.corner_radius = corner_radius
        self.show_pads = show_pads
        self._hex = BOARD_COLOR_CHOICES.get(color, color)
        self._outline_vertices: list[tuple[float, float]] | None = outline

        self._build_substrate()
        self.paint(self._hex)

    # -- geometry -----------------------------------------------------------

    def _build_substrate(self) -> None:
        sketch = Sketch(self.xy())
        if self._outline_vertices:
            pts = [Point(sketch, x, y) for x, y in self._outline_vertices]
            lines = [Line(p1=pts[i], p2=pts[(i + 1) % len(pts)]) for i in range(len(pts))]
            outline = Polygon(lines=lines)
        else:
            outline = Rectangle.from_center_and_sides(sketch.origin, self.width, self.height)
        self.add_operation(Extrusion(outline, self.thickness))

    @property
    def top_z(self) -> float:
        return self.thickness

    # -- drilling / footprints ---------------------------------------------

    def drill(self, x: float, y: float, diameter: float) -> "PCBBoard":
        """Cut a single round hole clean through the board at ``(x, y)``."""
        sketch = Sketch(self.xy())
        hole = Circle(Point(sketch, x, y), diameter / 2.0)
        # Extrude the cut slightly proud of both faces so it is unambiguously
        # a through hole regardless of floating-point board thickness.
        self.add_operation(
            Extrusion(hole, -0.1, self.thickness + 0.1, cut=True)
        )
        return self

    def apply_footprint(
        self, footprint: Footprint, x: float, y: float, rotation_deg: float = 0.0
    ) -> "PCBBoard":
        """Paint the copper lands of ``footprint`` placed at ``(x, y)`` and drill
        its through-hole pads. Surface-mount pads only paint; they never modify
        the board outline.

        Order matters: lands are painted **before** the holes are drilled, so the
        through-cut punches cleanly through both the board *and* the copper land,
        leaving a real annular pad with an open hole. (Drilling first and then
        painting a solid land would cap the hole back up.)"""
        placed: list[Pad] = footprint.transformed_pads(x, y, rotation_deg)
        if self.show_pads:
            paint_pads(self, placed, self.top_z)
        for pad in placed:
            if pad.is_through_hole:
                self.drill(pad.x, pad.y, pad.drill)
        return self


class RoundedPCBBoard(PCBBoard):
    """Convenience board with a default 3 mm corner radius for nicer outlines.

    (Corner rounding is approximated by the base rectangle for now; the radius
    is recorded for downstream silkscreen / outline tooling.)
    """

    def __init__(self, width: float, height: float, **kwargs):
        kwargs.setdefault("corner_radius", 3.0)
        super().__init__(width, height, **kwargs)


__all__ = ["PCBBoard", "RoundedPCBBoard", "COLORS", "BOARD_COLOR_CHOICES"]
