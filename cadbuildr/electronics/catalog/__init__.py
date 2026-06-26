"""Catalog layer: parts → packages → family generators, plus distributor
(Digi-Key) package-string parsing. This is what scales the library to thousands
of parts without thousands of classes."""

from .catalog import Catalog
from .digikey import PackageKey, parse_package_case
from .package import Package
from .part import Part

__all__ = ["Catalog", "Package", "Part", "PackageKey", "parse_package_case"]
