"""The footprint system — the single source of truth that ties a 3D component
body to the land pattern it needs on the PCB.

The whole point of this module is to make placement **non error-prone**. A
classic source of bugs in PCB design is the board and the populated assembly
drifting apart: you move a connector in the 3D model but forget to move (or
resize) the holes that were drilled for it, or vice-versa. Here a component and
its holes are described **once**, in the same place, and a single call wires up
*both* sides:

    pcb.place(PinHeader(rows=1, positions=8), ref="J1", x=20, y=5)

That one line:

1. cuts the header's drill pattern into the board ``Part`` (the *footprint*), and
2. seats the 3D header ``Part`` into the assembly at the matching transform.

Because both come from the same :class:`Footprint`, they can never disagree.

Two ways to attach a footprint to a component:

* subclass :class:`ElectronicComponent` and implement ``footprint()``; or
* decorate any ``Part`` with :func:`footprint` to attach a static land pattern.
"""

from __future__ import annotations

import math
from dataclasses import dataclass, field
from typing import Callable

from cadbuildr.foundation import (
    Circle,
    Extrusion,
    Part,
    Point,
    Sketch,
)

from .constants import COLORS, DEFAULT_COPPER_THICKNESS


@dataclass
class Pad:
    """A single connection point of a footprint, in the footprint's local frame
    (millimetres, origin at the part's reference point, +Z out of the board).

    A *through-hole* pad has ``drill > 0`` and punches a hole clean through the
    board. A *surface-mount* pad has ``drill == 0`` and only paints copper — it
    never modifies the board outline, which is exactly what we want for SMD.
    """

    x: float
    y: float
    drill: float = 0.0  # >0 → through-hole; 0 → SMD land
    pad_diameter: float = 0.0  # copper ring / land size (0 → auto from drill)
    name: str = ""  # optional pin name (e.g. "VCC", "1")

    @property
    def is_through_hole(self) -> bool:
        return self.drill > 0.0

    def effective_pad_diameter(self) -> float:
        if self.pad_diameter > 0.0:
            return self.pad_diameter
        if self.drill > 0.0:
            return self.drill + 0.9  # sensible annular ring
        return 1.5


@dataclass
class Footprint:
    """The land pattern for one component: where its pads sit and how big the
    holes are. Defined once and reused by the component, the board and the BOM.
    """

    name: str
    pads: list[Pad] = field(default_factory=list)
    # Courtyard = keep-out bounding box (width, height) for sanity / overlap
    # checks and silkscreen. Purely informational; never drilled.
    courtyard: tuple[float, float] = (0.0, 0.0)

    @property
    def is_surface_mount(self) -> bool:
        return all(not p.is_through_hole for p in self.pads)

    def transformed_pads(self, x: float, y: float, rotation_deg: float) -> list[Pad]:
        """Return this footprint's pads mapped onto the board, i.e. rotated by
        ``rotation_deg`` and translated to ``(x, y)``. Same maths the assembly
        uses to seat the body, so holes and body always line up."""
        theta = math.radians(rotation_deg)
        cos_t, sin_t = math.cos(theta), math.sin(theta)
        placed: list[Pad] = []
        for pad in self.pads:
            px = x + pad.x * cos_t - pad.y * sin_t
            py = y + pad.x * sin_t + pad.y * cos_t
            placed.append(
                Pad(
                    x=px,
                    y=py,
                    drill=pad.drill,
                    pad_diameter=pad.pad_diameter,
                    name=pad.name,
                )
            )
        return placed


# Convenience builders for the land patterns we use over and over. -----------


def grid_pads(
    rows: int,
    cols: int,
    pitch_x: float,
    pitch_y: float,
    drill: float,
    pad_diameter: float = 0.0,
) -> list[Pad]:
    """A ``rows × cols`` grid of identical pads, centred on the origin."""
    pads: list[Pad] = []
    x0 = -(cols - 1) * pitch_x / 2.0
    y0 = -(rows - 1) * pitch_y / 2.0
    n = 1
    for r in range(rows):
        for c in range(cols):
            pads.append(
                Pad(
                    x=x0 + c * pitch_x,
                    y=y0 + r * pitch_y,
                    drill=drill,
                    pad_diameter=pad_diameter,
                    name=str(n),
                )
            )
            n += 1
    return pads


def two_pad(spacing: float, drill: float, pad_diameter: float = 0.0) -> list[Pad]:
    """Two pads on the X axis ``spacing`` apart — axial parts, LEDs, caps."""
    return [
        Pad(-spacing / 2.0, 0.0, drill=drill, pad_diameter=pad_diameter, name="1"),
        Pad(spacing / 2.0, 0.0, drill=drill, pad_diameter=pad_diameter, name="2"),
    ]


class ElectronicComponent(Part):
    """Base class for every PCB part in the library.

    A component is a normal foundation ``Part`` (so it carries real 3D
    geometry) that additionally knows its own :class:`Footprint`. Subclasses
    build their body in ``__init__`` and implement :meth:`footprint`.

    ``seat_offset_z`` is the height of the part's local origin above the top
    copper of the board (usually 0 — the body sits *on* the board and its leads
    extend down through the holes).
    """

    seat_offset_z: float = 0.0

    def footprint(self) -> Footprint:  # pragma: no cover - abstract
        raise NotImplementedError(
            f"{type(self).__name__} must implement footprint()."
        )


def footprint(fp: Footprint | Callable[[Part], Footprint], *, seat_offset_z: float = 0.0):
    """Decorator that attaches a footprint to any ``Part`` subclass.

    Use it when a part does not derive from :class:`ElectronicComponent` but you
    still want it placeable with the dual-action ``PCB.place`` one-liner::

        @footprint(Footprint("CONN", pads=two_pad(5.0, drill=1.0)))
        class MyConnector(Part):
            ...

    ``fp`` may be a ready-made :class:`Footprint` or a callable taking the
    instance (for footprints that depend on instance parameters).
    """

    def decorate(cls: type) -> type:
        def _footprint(self) -> Footprint:
            return fp(self) if callable(fp) else fp

        cls.footprint = _footprint  # type: ignore[attr-defined]
        if not hasattr(cls, "seat_offset_z"):
            cls.seat_offset_z = seat_offset_z  # type: ignore[attr-defined]
        return cls

    return decorate


def paint_pads(board_part: Part, pads: list[Pad], z_top: float) -> None:
    """Paint thin copper lands on the top surface of the board for the given
    (already board-placed) pads. Purely cosmetic — does not change the outline.
    """
    sketch = Sketch(board_part.xy())
    for pad in pads:
        ring = Circle(Point(sketch, pad.x, pad.y), pad.effective_pad_diameter() / 2.0)
        board_part.add_operation(
            Extrusion(ring, z_top, z_top + DEFAULT_COPPER_THICKNESS)
        )


# Re-export a copper colour helper for boards that want to tint their pads.
COPPER_COLOR = COLORS.copper
