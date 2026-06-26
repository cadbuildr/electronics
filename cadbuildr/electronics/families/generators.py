"""Concrete package-family generators.

Each turns a nominal ``dims`` dict into a 3D body + an IPC-7351-derived land
pattern. We use single nominal dimensions (not min/max envelopes) — enough for
a mechanical / visual library — and the Nominal (N) density fillet goals from
``_ipc``. Adding a package is data (a row), not code; these few generators
cover the bulk of any catalogue.
"""

from __future__ import annotations

from typing import Any

from ..constants import COLORS, PITCH_100
from ..footprint import Footprint, Pad
from .._solids import add_box, add_pin_z
from . import _ipc
from .base import GeneratedComponent, PackageFamily, register


def _chip_land(dims) -> tuple[float, float, float]:
    """(pad_len, pad_wid, offset) for a 2-terminal chip from body L/W + band T."""
    body_l = dims["body_l"]
    body_w = dims["body_w"]
    term = dims.get("term_len", body_l * 0.22)
    fill = _ipc.CHIP[dims.get("density", "N")]
    land = _ipc.land_from_leads(body_l, term, body_w, fill)
    return land.pad_len, land.pad_wid, land.offset


class ChipFamily(PackageFamily):
    """2-terminal SMD chip — resistors (RESC) and MLCCs (CAPC)."""

    id = "chip"

    def build_body(self, part: GeneratedComponent, dims: dict[str, Any]) -> None:
        l, w, h = dims["body_l"], dims["body_w"], dims["body_h"]
        add_box(part, l, w, h, z0=0.0)
        part.paint(dims.get("color", COLORS.ic_black))

    def footprint(self, dims: dict[str, Any]) -> Footprint:
        pad_len, pad_wid, offset = _chip_land(dims)
        # pad_diameter carries the larger of the two pad dims for the round
        # cosmetic land; pads are SMD (drill 0).
        pd = max(pad_len, pad_wid)
        return Footprint(
            name=dims.get("ipc_name", f"RESC-{dims['body_l']}x{dims['body_w']}"),
            pads=[
                Pad(-offset, 0.0, drill=0.0, pad_diameter=pd, name="1"),
                Pad(offset, 0.0, drill=0.0, pad_diameter=pd, name="2"),
            ],
            courtyard=(2 * offset + pad_len + 0.5, pad_wid + 0.5),
        )


class GullwingDualFamily(PackageFamily):
    """Dual gull-wing SMD — SOIC / SOP / SSOP / TSSOP."""

    id = "gullwing_dual"

    def build_body(self, part: GeneratedComponent, dims: dict[str, Any]) -> None:
        per = dims["pins"] // 2
        body_l = dims.get("body_l", per * dims["pitch"] + 0.6)
        body_w = dims["body_w"]
        add_box(part, body_l, body_w, dims.get("body_h", 1.5), z0=0.1)
        part.paint(COLORS.ic_black)

    def footprint(self, dims: dict[str, Any]) -> Footprint:
        pins, pitch = dims["pins"], dims["pitch"]
        per = pins // 2
        fill = _ipc.GULLWING[dims.get("density", "N")]
        land = _ipc.land_from_leads(
            dims["lead_span"], dims["lead_len"], dims["lead_w"], fill
        )
        x0 = -(per - 1) * pitch / 2.0
        pads: list[Pad] = []
        n = 1
        pd = max(land.pad_len, land.pad_wid)
        for c in range(per):  # bottom row, left→right
            pads.append(Pad(x0 + c * pitch, -land.offset, drill=0.0, pad_diameter=pd, name=str(n))); n += 1
        for c in range(per - 1, -1, -1):  # top row, right→left
            pads.append(Pad(x0 + c * pitch, land.offset, drill=0.0, pad_diameter=pd, name=str(n))); n += 1
        return Footprint(
            name=dims.get("ipc_name", f"SOIC-{pins}"),
            pads=pads,
            courtyard=(per * pitch + 1.0, 2 * land.offset + land.pad_len + 0.5),
        )


class GullwingQuadFamily(PackageFamily):
    """Quad gull-wing SMD — QFP / LQFP / TQFP (gull-wing goals on all 4 sides)."""

    id = "gullwing_quad"

    def build_body(self, part: GeneratedComponent, dims: dict[str, Any]) -> None:
        body = dims["body"]
        add_box(part, body, body, dims.get("body_h", 1.4), z0=0.1)
        part.paint(COLORS.ic_black)

    def footprint(self, dims: dict[str, Any]) -> Footprint:
        pins, pitch = dims["pins"], dims["pitch"]
        per = pins // 4
        fill = _ipc.GULLWING[dims.get("density", "N")]
        land = _ipc.land_from_leads(
            dims["lead_span"], dims["lead_len"], dims["lead_w"], fill
        )
        pd = max(land.pad_len, land.pad_wid)
        x0 = -(per - 1) * pitch / 2.0
        pads: list[Pad] = []
        n = 1
        for c in range(per):  # bottom
            pads.append(Pad(x0 + c * pitch, -land.offset, drill=0.0, pad_diameter=pd, name=str(n))); n += 1
        for c in range(per):  # right
            pads.append(Pad(land.offset, x0 + c * pitch, drill=0.0, pad_diameter=pd, name=str(n))); n += 1
        for c in range(per - 1, -1, -1):  # top
            pads.append(Pad(x0 + c * pitch, land.offset, drill=0.0, pad_diameter=pd, name=str(n))); n += 1
        for c in range(per - 1, -1, -1):  # left
            pads.append(Pad(-land.offset, x0 + c * pitch, drill=0.0, pad_diameter=pd, name=str(n))); n += 1
        return Footprint(
            name=dims.get("ipc_name", f"QFP-{pins}"),
            pads=pads,
            courtyard=(2 * land.offset + land.pad_len + 1.0,) * 2,
        )


class DualInlineFamily(PackageFamily):
    """Through-hole DIP — IPC-7251 holes + annular pads."""

    id = "dip"

    def build_body(self, part: GeneratedComponent, dims: dict[str, Any]) -> None:
        per = dims["pins"] // 2
        pitch = dims.get("pitch", PITCH_100)
        row = dims["row_mm"]
        body_len = per * pitch
        add_box(part, body_len, row - 1.5, 3.5, z0=0.5)
        part.paint(COLORS.ic_black)
        for pad in self.footprint(dims).pads:
            add_pin_z(part, pad.x, pad.y, 0.5, top=0.8, bottom=-3.2)
        part.paint(COLORS.ic_black)

    def footprint(self, dims: dict[str, Any]) -> Footprint:
        per = dims["pins"] // 2
        pitch = dims.get("pitch", PITCH_100)
        row = dims["row_mm"]
        drill = _ipc.through_hole_drill(dims.get("lead_d", 0.5))
        pad_d = _ipc.annular_pad(drill)
        x0 = -(per - 1) * pitch / 2.0
        pads: list[Pad] = []
        n = 1
        for c in range(per):
            pads.append(Pad(x0 + c * pitch, -row / 2.0, drill=drill, pad_diameter=pad_d, name=str(n))); n += 1
        for c in range(per - 1, -1, -1):
            pads.append(Pad(x0 + c * pitch, row / 2.0, drill=drill, pad_diameter=pad_d, name=str(n))); n += 1
        return Footprint(
            name=dims.get("ipc_name", f"DIP-{dims['pins']}"),
            pads=pads,
            courtyard=(per * pitch + 1.0, row + 2.0),
        )


# Register the built-in families.
register(ChipFamily())
register(GullwingDualFamily())
register(GullwingQuadFamily())
register(DualInlineFamily())

__all__ = [
    "ChipFamily",
    "GullwingDualFamily",
    "GullwingQuadFamily",
    "DualInlineFamily",
]
