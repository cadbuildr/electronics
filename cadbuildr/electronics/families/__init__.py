"""Parametric package-family generators (the bounded geometry engine)."""

from .base import GeneratedComponent, PackageFamily, families, get_family, register

# Importing registers the built-in families.
from . import generators  # noqa: F401,E402

__all__ = [
    "GeneratedComponent",
    "PackageFamily",
    "register",
    "get_family",
    "families",
]
