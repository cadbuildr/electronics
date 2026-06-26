"""The :class:`Catalog` — resolves parts and distributor package strings to
generated geometry. This is the scale layer:

    K family generators  ◀──  M packages (data)  ◀──  N parts (data)
        (a dozen)              (hundreds)               (thousands+)

Packages are loaded from ``data/packages.json`` and parts (optionally) from a
CSV. Both are plain data, so growing the catalogue means adding rows, not code.
"""

from __future__ import annotations

import csv
import json
from pathlib import Path
from typing import Iterable, Optional

from ..families import GeneratedComponent
from .digikey import PackageKey, parse_package_case
from .package import Package
from .part import Part

_DATA = Path(__file__).resolve().parent.parent / "data"


class Catalog:
    def __init__(self, packages: Iterable[Package] = (), parts: Iterable[Part] = ()):
        self.packages: dict[str, Package] = {p.code: p for p in packages}
        self.parts: dict[str, Part] = {p.mpn: p for p in parts}

    # -- loading ------------------------------------------------------------

    @classmethod
    def load(
        cls,
        packages_json: Optional[Path] = None,
        parts_csv: Optional[Path] = None,
    ) -> "Catalog":
        cat = cls()
        cat.load_packages(packages_json or _DATA / "packages.json")
        if parts_csv is None:
            parts_csv = _DATA / "parts.csv"
        if Path(parts_csv).exists():
            cat.load_parts(parts_csv)
        return cat

    def load_packages(self, path: Path) -> None:
        rows = json.loads(Path(path).read_text())
        for code, row in rows.items():
            self.packages[code] = Package(
                code=code,
                family=row["family"],
                dims=row.get("dims", {}),
                mounting=row.get("mounting", "smd"),
                ipc_name=row.get("ipc_name", ""),
                kicad_fp=row.get("kicad_fp", ""),
                jedec=row.get("jedec", ""),
                description=row.get("description", ""),
            )

    def load_parts(self, path: Path) -> None:
        with open(path, newline="") as fh:
            for row in csv.DictReader(fh):
                fixed = {"mpn", "category", "package", "manufacturer"}
                attrs = {k: v for k, v in row.items() if k not in fixed and v != ""}
                self.parts[row["mpn"]] = Part(
                    mpn=row["mpn"],
                    category=row.get("category", ""),
                    package=row["package"],
                    manufacturer=row.get("manufacturer", ""),
                    attrs=attrs,
                )

    # -- lookup / build -----------------------------------------------------

    def package(self, code: str) -> Package:
        try:
            return self.packages[code]
        except KeyError:
            raise KeyError(f"Unknown package {code!r}") from None

    def build_package(self, code: str) -> GeneratedComponent:
        return self.package(code).build()

    def build_part(self, mpn: str) -> GeneratedComponent:
        """Resolve a part -> its package -> a 3D component, applying any
        cosmetic colour attribute."""
        part = self.parts[mpn]
        comp = self.package(part.package).build()
        color = part.color()
        if color:
            comp.paint(color)
        return comp

    # -- distributor mapping ------------------------------------------------

    def resolve_package_case(
        self, package_case: str, *, mounting: str = "", supplier_device_package: str = ""
    ) -> Optional[Package]:
        """Map a Digi-Key ``Package / Case`` string onto a catalogue package,
        by parsing it to a :class:`PackageKey` and matching family + size."""
        key = parse_package_case(
            package_case, mounting=mounting, supplier_device_package=supplier_device_package
        )
        if key is None:
            return None
        return self._match_key(key)

    def _match_key(self, key: PackageKey) -> Optional[Package]:
        best: Optional[Package] = None
        for pkg in self.packages.values():
            if pkg.family != key.family:
                continue
            # size match: metric chip code, or a name substring
            if key.size and key.size not in (pkg.dims.get("size", ""), pkg.code, pkg.jedec):
                if key.size.upper() not in pkg.code.upper():
                    continue
            if key.pins is not None and pkg.dims.get("pins") not in (None, key.pins):
                continue
            best = pkg
            if key.pins is None or pkg.dims.get("pins") == key.pins:
                return pkg
        return best


__all__ = ["Catalog"]
