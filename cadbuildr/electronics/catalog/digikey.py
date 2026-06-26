"""Parse Digi-Key ``Package / Case`` strings into a normalized geometry key.

The scaling insight (validated against Digi-Key's catalog): ~18 M part numbers
collapse onto a few thousand named footprints and only a few dozen *package
families*, because **geometry is a pure function of Package/Case + Mounting
Type + pin count + pitch — never the electrical value**. So the catalog layer
only needs to turn a distributor's package string into a
:class:`PackageKey` ``(family, size, pins, pitch, mounting)`` and hand that to a
generator.

Digi-Key writes these strings inconsistently; the rules encoded here come from
real product pages:

* two-terminal passives: ``0805 (2012 Metric)`` — imperial leading, metric in
  parens with the literal word "Metric";
* ICs: ``8-SOIC (0.154", 3.90mm Width)`` / ``8-DIP (0.300", 7.62mm)`` — lead
  count prefix + dimensional detail;
* transistors/diodes: ``TO-236-3, SC-59, SOT-23-3`` — several equivalent
  standard names comma-joined (treat each as an alias of one family);
* punctuation drift: ``DO-214AC, SMA`` == ``DO-214AC (SMA)``.

Per Digi-Key's API User Agreement we do **not** cache their attribute *data*;
this module only parses the *string format* (a non-copyrightable schema) so a
user can map their own BOM/lookup results onto our generated geometry.
"""

from __future__ import annotations

import re
from dataclasses import dataclass, field
from typing import Optional


@dataclass(frozen=True)
class PackageKey:
    """The bounded geometry key a generator family consumes."""

    family: str  # "chip", "gullwing_dual", "gullwing_quad", "dip", "sot", "to", ...
    size: str = ""  # metric chip code ("2012"), or canonical package ("SOIC", "DO-214AC")
    pins: Optional[int] = None
    pitch_mm: Optional[float] = None
    mounting: str = ""  # "smd" | "tht" | ""
    aliases: tuple[str, ...] = field(default_factory=tuple)
    raw: str = ""


# Imperial chip code -> metric code (EIA). Geometry is keyed on the metric body.
CHIP_IMPERIAL_TO_METRIC = {
    "0201": "0603",
    "0402": "1005",
    "0603": "1608",
    "0805": "2012",
    "1206": "3216",
    "1210": "3225",
    "1812": "4532",
    "2010": "5025",
    "2512": "6332",
}

# Standard two-/three-terminal package names -> family.
_NAMED_FAMILY = {
    "SOIC": "gullwing_dual",
    "SO": "gullwing_dual",
    "SOP": "gullwing_dual",
    "SSOP": "gullwing_dual",
    "TSSOP": "gullwing_dual",
    "MSOP": "gullwing_dual",
    "TSOP": "gullwing_dual",
    "QFP": "gullwing_quad",
    "LQFP": "gullwing_quad",
    "TQFP": "gullwing_quad",
    "QFN": "nolead",
    "DFN": "nolead",
    "DIP": "dip",
    "PDIP": "dip",
    "CDIP": "dip",
    "SOT-23": "sot",
    "SOT-223": "sot",
    "SOT-89": "sot",
    "TO-236": "sot",
    "SC-59": "sot",
    "SC-70": "sot",
    "TO-92": "to",
    "TO-220": "to",
    "TO-247": "to",
    "TO-263": "to",  # D2PAK (SMD power)
    "TO-252": "to",  # DPAK
    "DO-214AC": "chip2_smd",  # SMA
    "DO-214AA": "chip2_smd",  # SMB
    "DO-214AB": "chip2_smd",  # SMC
    "DO-35": "axial",
    "DO-41": "axial",
    "SOD-123": "chip2_smd",
    "SOD-323": "chip2_smd",
    "HC-49": "crystal_hc49",
}

_LEADCOUNT_RE = re.compile(r"^\s*(\d+)\s*-\s*([A-Za-z]+)")
_CHIP_RE = re.compile(r"^\s*(\d{4})\s*\(\s*(\d{4})\s*Metric\s*\)", re.IGNORECASE)
_DIP_ROW_RE = re.compile(r"([\d.]+)\s*mm")
_SOIC_WIDTH_RE = re.compile(r"([\d.]+)\s*mm\s*Width", re.IGNORECASE)


def _normalize_token(tok: str) -> str:
    return tok.strip().upper().replace("(", "").replace(")", "")


def parse_package_case(
    package_case: str, *, mounting: str = "", supplier_device_package: str = ""
) -> Optional[PackageKey]:
    """Map a Digi-Key ``Package / Case`` string (optionally plus Mounting Type
    and Supplier Device Package) onto a :class:`PackageKey`, or ``None`` if the
    family is not recognised.
    """
    if not package_case:
        package_case = supplier_device_package
    raw = package_case.strip()
    mount = _mounting(mounting)

    # 1) two-terminal chip passive: "0805 (2012 Metric)"
    m = _CHIP_RE.match(raw)
    if m:
        metric = m.group(2)
        return PackageKey(family="chip", size=metric, pins=2, mounting=mount or "smd", raw=raw)

    # 2) lead-count prefixed IC: "8-SOIC (...)", "28-TQFP (...)", "8-DIP (...)"
    m = _LEADCOUNT_RE.match(raw)
    if m:
        pins = int(m.group(1))
        fam_name = m.group(2).upper()
        family = _NAMED_FAMILY.get(fam_name)
        if family:
            pitch = None
            extra = {}
            if family == "dip":
                row = _DIP_ROW_RE.search(raw)
                if row:
                    extra["row_mm"] = float(row.group(1))
            return PackageKey(
                family=family,
                size=fam_name,
                pins=pins,
                pitch_mm=pitch,
                mounting=mount or ("tht" if family == "dip" else "smd"),
                raw=raw,
            )

    # 3) comma-joined aliases: "TO-236-3, SC-59, SOT-23-3"
    tokens = [t for t in (_normalize_token(t) for t in re.split(r"[;,]", raw)) if t]
    pins = _trailing_pincount(tokens)
    for tok in tokens:
        base = _strip_pincount(tok)
        family = _NAMED_FAMILY.get(base)
        if family:
            return PackageKey(
                family=family,
                size=base,
                pins=pins,
                mounting=mount or _default_mount(family),
                aliases=tuple(tokens),
                raw=raw,
            )

    # 4) single canonical name without lead prefix, e.g. "DO-214AC, SMA"
    for tok in tokens:
        for name, family in _NAMED_FAMILY.items():
            if tok.startswith(name.upper()):
                return PackageKey(
                    family=family, size=name, mounting=mount or _default_mount(family),
                    aliases=tuple(tokens), raw=raw,
                )
    return None


def _mounting(s: str) -> str:
    s = (s or "").strip().lower()
    if "surface" in s or s == "smd" or s == "smt":
        return "smd"
    if "through" in s or s == "tht" or "thru" in s:
        return "tht"
    return ""


def _default_mount(family: str) -> str:
    return {"dip": "tht", "to": "tht", "axial": "tht", "crystal_hc49": "tht"}.get(family, "smd")


def _trailing_pincount(tokens: list[str]) -> Optional[int]:
    for tok in tokens:
        m = re.search(r"-(\d+)$", tok)
        if m:
            return int(m.group(1))
    return None


def _strip_pincount(tok: str) -> str:
    return re.sub(r"-\d+$", "", tok)


__all__ = ["PackageKey", "parse_package_case", "CHIP_IMPERIAL_TO_METRIC"]
