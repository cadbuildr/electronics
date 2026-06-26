"""IPC-7351B land-pattern math, simplified for a 3D-body library.

We generate SMD lands from package lead geometry + the three density-level
fillet goals (toe ``Jt``, heel ``Jh``, side ``Js``). The full standard adds an
RMS tolerance term (``sqrt(Ltol² + Ftol² + Ptol²)``); for a visual / mechanical
library the nominal goals alone give correct, recognisable lands, so we drop
the RMS term and document it.

Per-side gull-wing land (also used for 2-terminal chips with N=1):

    Z = L + 2·Jt        # outer pad-to-outer pad span
    S = L - 2·T         # inner lead span (gap between inner foot edges)
    G = S - 2·Jh        # inner pad-to-inner pad gap
    pad_len  = (Z - G) / 2
    pad_offs = (Z + G) / 4      # pad centre, measured from package centre
    pad_wid  = W + 2·Js
"""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class Fillet:
    """Toe / heel / side fillet goals (mm) for one density level."""

    toe: float
    heel: float
    side: float


# Density levels: Most (A), Nominal (B), Least (C). Nominal is the default.
# Values are the widely-used IPC-7351B goals for gull-wing leads; chip
# (RESC/CAPC) uses its own smaller goals.
GULLWING = {
    "M": Fillet(0.55, 0.45, 0.05),
    "N": Fillet(0.35, 0.35, 0.03),
    "L": Fillet(0.15, 0.25, 0.01),
}
CHIP = {
    "M": Fillet(0.20, 0.00, 0.05),
    "N": Fillet(0.10, 0.00, 0.00),
    "L": Fillet(0.00, -0.05, -0.05),
}


@dataclass(frozen=True)
class Land:
    pad_len: float  # radial pad dimension (along the lead)
    pad_wid: float  # tangential pad dimension
    offset: float  # pad centre distance from package centreline


def land_from_leads(
    lead_span: float, lead_len: float, lead_wid: float, fillet: Fillet
) -> Land:
    """Compute one row's pad size + placement from lead geometry + fillet goals."""
    z = lead_span + 2 * fillet.toe
    s = lead_span - 2 * lead_len
    g = s - 2 * fillet.heel
    return Land(
        pad_len=(z - g) / 2.0,
        pad_wid=lead_wid + 2 * fillet.side,
        offset=(z + g) / 4.0,
    )


def through_hole_drill(lead_diameter: float) -> float:
    """IPC-7251 hole = lead Ø + clearance (Nominal/Level-B clearance ≈0.2 mm;
    we use 0.25 for hand-insert friendliness)."""
    return round(lead_diameter + 0.25, 2)


def annular_pad(drill: float, ring: float = 0.30) -> float:
    """IPC-7251 THT pad Ø = hole + 2·(min ring + fab allowance). The
    Nominal/Level-B total works out to ≈ hole + 0.6 mm (ring 0.3 per side)."""
    return drill + 2 * ring


__all__ = ["Fillet", "Land", "GULLWING", "CHIP", "land_from_leads",
           "through_hole_drill", "annular_pad"]
