"""Package *families* — the bounded set of parametric generators.

This is the engine that makes the library scale to catalog size. The key fact
(validated against Digi-Key): millions of part numbers collapse onto a few
thousand named footprints and only a few dozen *families*, because geometry is
a pure function of ``Package/Case + Mounting + pins + pitch``. So we write one
generator per family and feed it a small ``dims`` dict; a 10 kΩ and a 4.7 kΩ
0805 resistor are the *same* generated geometry.

A :class:`PackageFamily` turns a ``dims`` dict into both halves a component
needs — the 3D body (operations on a ``Part``) and the land pattern
(:class:`~cadbuildr.electronics.footprint.Footprint`) — keeping them in lock
step from one dimension set, exactly as KiCad's footprint + 3D generators do.
"""

from __future__ import annotations

from abc import ABC, abstractmethod
from typing import Any

from ..footprint import ElectronicComponent, Footprint


class PackageFamily(ABC):
    """One parametric generator (chip, gull-wing dual, QFP, DIP, ...)."""

    id: str = ""

    @abstractmethod
    def footprint(self, dims: dict[str, Any]) -> Footprint:
        """Build the land pattern (pads/holes) from ``dims``."""

    @abstractmethod
    def build_body(self, part: "GeneratedComponent", dims: dict[str, Any]) -> None:
        """Add the 3D body operations (and paint) to ``part``."""

    def seat_offset_z(self, dims: dict[str, Any]) -> float:
        """Height of the part origin above the board top (0 = sits on board)."""
        return 0.0


_REGISTRY: dict[str, PackageFamily] = {}


def register(family: PackageFamily) -> PackageFamily:
    """Register a family instance under its ``id``."""
    if not family.id:
        raise ValueError("PackageFamily needs a non-empty id")
    _REGISTRY[family.id] = family
    return family


def get_family(family_id: str) -> PackageFamily:
    try:
        return _REGISTRY[family_id]
    except KeyError:
        raise KeyError(
            f"Unknown package family {family_id!r}. Registered: {sorted(_REGISTRY)}"
        ) from None


def families() -> list[str]:
    return sorted(_REGISTRY)


class GeneratedComponent(ElectronicComponent):
    """An :class:`ElectronicComponent` whose body + footprint come from a
    :class:`PackageFamily` and a ``dims`` dict, instead of bespoke code.

    This is what a catalog package instantiates, so thousands of parts reuse a
    handful of generators.
    """

    def __init__(self, family_id: str, dims: dict[str, Any]):
        super().__init__()
        self._family = get_family(family_id)
        self._dims = dict(dims)
        self.seat_offset_z = self._family.seat_offset_z(self._dims)
        self._family.build_body(self, self._dims)

    def footprint(self) -> Footprint:
        return self._family.footprint(self._dims)


__all__ = [
    "PackageFamily",
    "GeneratedComponent",
    "register",
    "get_family",
    "families",
]
