"""A *package* — one bounded geometry instance (a family + dimensions + the
industry names it is known by). The catalog has hundreds of these; they are
shared by thousands of parts.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

from ..families import GeneratedComponent


@dataclass
class Package:
    """A standard package: the geometry key plus its canonical names.

    ``dims`` are the parameters the family generator consumes; ``ipc_name`` /
    ``kicad_fp`` / ``jedec`` are the cross-references documented in
    ``docs/COMPONENT_REFERENCE.md``.
    """

    code: str  # our short id, e.g. "R_0805", "SOIC-8", "DIP-8_W7.62"
    family: str  # a registered PackageFamily id
    dims: dict[str, Any] = field(default_factory=dict)
    mounting: str = "smd"  # "smd" | "tht"
    ipc_name: str = ""
    kicad_fp: str = ""
    jedec: str = ""
    description: str = ""

    def build(self) -> GeneratedComponent:
        """Instantiate the 3D component (body + footprint) for this package."""
        return GeneratedComponent(self.family, self.dims)


__all__ = ["Package"]
