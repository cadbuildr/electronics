"""The :class:`PCB` assembly — a reusable template that owns a board and the
components placed on it, and keeps the two in lock-step.

This is the "dual class" the request is about: a :class:`PCB` is a foundation
``Assembly`` (so it renders the populated board) that *also* manages the
underlying :class:`PCBBoard` ``Part``. Every :meth:`place` call drives both
sides at once, so the holes in the board and the bodies in the assembly can
never drift apart.

Two equivalent styles are supported:

* **Imperative / builder** — create the board, then add parts one line at a
  time::

      pcb = PCB(80, 60, color="blue")
      pcb.place(PinHeader(positions=8), ref="J1", x=-30, y=25)
      pcb.place(Resistor(resistance="220"), ref="R1", x=0, y=0)

* **Declarative** — hand a list of :class:`Placement`\\s (the "standard
  format" of components + placements) to :meth:`from_placements`::

      PCB.from_placements(80, 60, [
          Placement(PinHeader(positions=8), "J1", -30, 25),
          Placement(Resistor("220"), "R1", 0, 0, rotation=90),
      ])
"""

from __future__ import annotations

import math
from dataclasses import dataclass, field

from cadbuildr.foundation import Assembly, TFHelper

from .board import PCBBoard
from .constants import DEFAULT_BOARD_THICKNESS
from .footprint import ElectronicComponent, Footprint


class Components(Assembly):
    """Sub-assembly that groups all placed electronic components on a PCB.

    Having a dedicated sub-assembly means the entire component population can
    be hidden or shown as a single tree node in the viewer — and the viewer
    can default boards to showing only the bare substrate.
    """


@dataclass
class Placement:
    """One component placed on the board: the part, a reference designator and
    a pose in the board plane (millimetres / degrees)."""

    component: ElectronicComponent
    ref: str
    x: float
    y: float
    rotation: float = 0.0  # degrees, about +Z
    side: str = "top"  # "top" or "bottom"


@dataclass
class BomLine:
    ref: str
    component: str
    footprint: str
    x: float
    y: float
    rotation: float
    side: str


class PCB(Assembly):
    """A populated printed-circuit board: a board plus its components."""

    def __init__(
        self,
        width: float,
        height: float,
        thickness: float = DEFAULT_BOARD_THICKNESS,
        color: str = "green",
        name: str = "PCB",
        show_pads: bool = True,
        outline: list[tuple[float, float]] | None = None,
    ):
        super().__init__()
        self.width = width
        self.height = height
        self.thickness = thickness
        self.board = PCBBoard(
            width,
            height,
            thickness=thickness,
            color=color,
            show_pads=show_pads,
            outline=outline,
        )
        self.placements: list[Placement] = []
        # Add the board first, then a dedicated sub-assembly for components.
        # The sub-assembly groups all placed parts so the viewer can hide them
        # all at once via the "components" tree node.
        #
        # NB: ``add_component`` converts its argument to a *root* eagerly — and
        # the conversion snapshots the component's state. If we added the board
        # (or an empty components assembly) eagerly here, later mutations would
        # be lost: every drill/pad ``place()`` adds to the board, and every part
        # it adds to the sub-assembly, would never reach the rendered DAG. So we
        # append *live references* to both; ``show_dag``/``to_dag`` convert them
        # at serialisation time, capturing the fully-drilled board and the
        # fully-populated component list.
        self._components_asm = Components()
        self.components.append(self.board)
        self.components.append(self._components_asm)

    # -- the dual-action one-liner -----------------------------------------

    def place(
        self,
        component: ElectronicComponent,
        ref: str,
        x: float,
        y: float,
        rotation: float = 0.0,
        side: str = "top",
    ) -> "PCB":
        """Place ``component`` at ``(x, y)`` rotated ``rotation`` degrees.

        This single call does *both* halves of the job:

        1. **board** — drills the component's footprint into :attr:`board`; and
        2. **assembly** — seats the 3D body at the matching transform.

        Returns ``self`` so calls can be chained.
        """
        fp: Footprint = component.footprint()

        # 1) board side — drill / paint the land pattern.
        self.board.apply_footprint(fp, x, y, rotation)

        # 2) assembly side — seat the body with the same pose inside the
        #    Components sub-assembly so the viewer tree can toggle them together.
        tf = TFHelper()
        seat = getattr(component, "seat_offset_z", 0.0)
        if side == "bottom":
            tf.rotate([1.0, 0.0, 0.0], math.pi)  # flip onto the underside
            tf.translate([x, y, -seat])
        else:
            tf.rotate([0.0, 0.0, 1.0], math.radians(rotation))
            tf.translate([x, y, self.thickness + seat])
        self._components_asm.add_component(component, tf.get_tf())

        self.placements.append(Placement(component, ref, x, y, rotation, side))
        return self

    # -- declarative construction ------------------------------------------

    @classmethod
    def from_placements(
        cls,
        width: float,
        height: float,
        placements: list[Placement],
        thickness: float = DEFAULT_BOARD_THICKNESS,
        color: str = "green",
        name: str = "PCB",
    ) -> "PCB":
        """Build a fully-populated board from a list of placements."""
        board = cls(width, height, thickness=thickness, color=color, name=name)
        for p in placements:
            board.place(p.component, p.ref, p.x, p.y, p.rotation, p.side)
        return board

    # -- mounting holes -----------------------------------------------------

    def mounting_hole(self, x: float, y: float, diameter: float = 3.2) -> "PCB":
        """Drill a bare mounting hole (default M3 clearance) in the board."""
        self.board.drill(x, y, diameter)
        return self

    def mounting_holes_rect(
        self, inset_x: float, inset_y: float, diameter: float = 3.2
    ) -> "PCB":
        """Drill four mounting holes inset from each corner of the board."""
        hx = self.width / 2.0 - inset_x
        hy = self.height / 2.0 - inset_y
        for sx in (-1, 1):
            for sy in (-1, 1):
                self.mounting_hole(sx * hx, sy * hy, diameter)
        return self

    # -- bill of materials --------------------------------------------------

    def bom(self) -> list[BomLine]:
        """The placement list as a flat, serialisable bill of materials."""
        return [
            BomLine(
                ref=p.ref,
                component=type(p.component).__name__,
                footprint=p.component.footprint().name,
                x=p.x,
                y=p.y,
                rotation=p.rotation,
                side=p.side,
            )
            for p in self.placements
        ]


__all__ = ["PCB", "Placement", "BomLine", "Components"]
