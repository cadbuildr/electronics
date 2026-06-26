"""A *part* — a thin metadata record (MPN + a package reference + electrical /
cosmetic attributes). The catalog has thousands of these; each points at one
shared :class:`~cadbuildr.electronics.catalog.package.Package`.

Per Digi-Key's API User Agreement we don't ship their attribute *data*; parts
here are user-supplied or datasheet-derived rows.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any


@dataclass
class Part:
    """One catalogue line. ``package`` is a :class:`Package` code; ``attrs``
    are electrical (value, voltage, …) or cosmetic (color) and never affect
    geometry — only the shared package does."""

    mpn: str
    category: str
    package: str
    manufacturer: str = ""
    attrs: dict[str, Any] = field(default_factory=dict)

    # Cosmetic attribute keys applied to the built component, if present.
    COSMETIC_COLOR_KEYS = ("color", "body_color")

    def color(self) -> str | None:
        for key in self.COSMETIC_COLOR_KEYS:
            if self.attrs.get(key):
                return str(self.attrs[key])
        return None


__all__ = ["Part"]
