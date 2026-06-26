"""CADbuildr PCB — 3D models of common printed-circuit-board components plus a
reusable framework for assembling them into boards.

Two halves:

* **Components** — parametric 3D parts (resistors, capacitors, LEDs, headers,
  USB / Ethernet connectors, ICs, crystals, ...), each of which carries its own
  :class:`~cadbuildr.electronics.footprint.Footprint`.

* **Assembly** — :class:`~cadbuildr.electronics.pcb.PCB`, a template that owns a
  :class:`~cadbuildr.electronics.board.PCBBoard` and places components with a
  single dual-action call that keeps the board holes and the 3D bodies in sync.

Quick start::

    from cadbuildr.foundation import show
    from cadbuildr.electronics import PCB, PinHeader, Resistor, LED

    pcb = PCB(50, 30, color="blue")
    pcb.place(PinHeader(positions=6), ref="J1", x=-18, y=10)
    pcb.place(Resistor("220"), ref="R1", x=0, y=0)
    pcb.place(LED("red"), ref="D1", x=12, y=0)
    show(pcb)
"""

from __future__ import annotations

from .constants import COLORS, BOARD_COLOR_CHOICES, LED_COLOR_CHOICES
from .footprint import (
    ElectronicComponent,
    Footprint,
    Pad,
    footprint,
    grid_pads,
    two_pad,
)
from .board import PCBBoard, RoundedPCBBoard
from .pcb import PCB, Components, Placement, BomLine
from .components import (
    Resistor,
    ResistorSMD,
    CeramicCapacitor,
    ElectrolyticCapacitor,
    LED,
    Diode,
    PinHeader,
    ScrewTerminal,
    USBTypeA,
    USBMicroB,
    RJ45,
    BarrelJack,
    DIP,
    SOIC,
    QFP,
    Crystal,
    TactileButton,
)

# Scale layer: data-driven catalog (parts → packages → family generators) and
# the parametric generators behind it. Lets the library grow to catalogue size
# by adding data rows, not classes. See docs/SCALING.md.
from .families import GeneratedComponent, PackageFamily, families
from .catalog import Catalog, Package, Part, PackageKey, parse_package_case

# Parametric @cadbuildr_project entry points (best-effort: needs a foundation
# new enough to expose the SDK parameter decorators).
try:
    from .projects import demo_board, header_strip, blinky
except Exception:  # pragma: no cover - older pinned foundations
    demo_board = header_strip = blinky = None  # type: ignore[assignment]

__all__ = [
    "COLORS",
    "BOARD_COLOR_CHOICES",
    "LED_COLOR_CHOICES",
    # framework
    "ElectronicComponent",
    "Footprint",
    "Pad",
    "footprint",
    "grid_pads",
    "two_pad",
    "PCBBoard",
    "RoundedPCBBoard",
    "PCB",
    "Components",
    "Placement",
    "BomLine",
    # components
    "Resistor",
    "ResistorSMD",
    "CeramicCapacitor",
    "ElectrolyticCapacitor",
    "LED",
    "Diode",
    "PinHeader",
    "ScrewTerminal",
    "USBTypeA",
    "USBMicroB",
    "RJ45",
    "BarrelJack",
    "DIP",
    "SOIC",
    "QFP",
    "Crystal",
    "TactileButton",
    # scale layer
    "GeneratedComponent",
    "PackageFamily",
    "families",
    "Catalog",
    "Package",
    "Part",
    "PackageKey",
    "parse_package_case",
    # projects
    "demo_board",
    "header_strip",
    "blinky",
]
