"""Tests for the scale layer: families, packages, parts and Digi-Key parsing."""

from __future__ import annotations

import pytest

from cadbuildr.electronics import Catalog, GeneratedComponent, families, parse_package_case
from cadbuildr.electronics.families import get_family


@pytest.fixture(scope="module")
def cat() -> Catalog:
    return Catalog.load()


def test_families_registered():
    assert {"chip", "gullwing_dual", "gullwing_quad", "dip"} <= set(families())


def test_catalog_loads(cat):
    assert len(cat.packages) >= 10
    assert len(cat.parts) >= 5


@pytest.mark.parametrize(
    "mpn,package,expect_th",
    [
        ("RC0805FR-0710KL", "R_0805", 0),
        ("NE555P", "DIP-8", 8),
        ("ATMEGA328P-PU", "DIP-28", 28),
        ("ATMEGA328P-AU", "TQFP-32", 0),
        ("LM358DR", "SOIC-8", 0),
        ("STM32F103RBT6", "LQFP-64", 0),
    ],
)
def test_build_part(cat, mpn, package, expect_th):
    comp = cat.build_part(mpn)
    assert isinstance(comp, GeneratedComponent)
    assert cat.parts[mpn].package == package
    fp = comp.footprint()
    th = sum(1 for p in fp.pads if p.is_through_hole)
    assert th == expect_th
    assert isinstance(comp.to_dag(), dict)


def test_pin_counts_match_package(cat):
    # The generated footprint pad count equals the package pin count.
    for code in ("DIP-8", "SOIC-8", "TQFP-32", "LQFP-64"):
        pkg = cat.package(code)
        fp = pkg.build().footprint()
        assert len(fp.pads) == pkg.dims["pins"]


def test_chip_is_smd_two_pad(cat):
    fp = cat.package("R_0805").build().footprint()
    assert len(fp.pads) == 2
    assert fp.is_surface_mount


@pytest.mark.parametrize(
    "string,mounting,family,pins",
    [
        ("0805 (2012 Metric)", "Surface Mount", "chip", 2),
        ("0603 (1608 Metric)", "Surface Mount", "chip", 2),
        ('8-SOIC (0.154", 3.90mm Width)', "Surface Mount", "gullwing_dual", 8),
        ('8-DIP (0.300", 7.62mm)', "Through Hole", "dip", 8),
        ("28-TQFP (7x7)", "Surface Mount", "gullwing_quad", 28),
        ("TO-236-3, SC-59, SOT-23-3", "Surface Mount", "sot", 3),
        ("TO-220-3", "Through Hole", "to", 3),
    ],
)
def test_digikey_parse(string, mounting, family, pins):
    key = parse_package_case(string, mounting=mounting)
    assert key is not None
    assert key.family == family
    assert key.pins == pins


def test_digikey_resolves_to_package(cat):
    assert cat.resolve_package_case("0805 (2012 Metric)", mounting="Surface Mount").code == "R_0805"
    assert cat.resolve_package_case('8-DIP (0.300", 7.62mm)', mounting="Through Hole").code == "DIP-8"
    # We have no 28-pin QFP package, so resolution returns None (correct).
    assert cat.resolve_package_case("28-TQFP (7x7)", mounting="Surface Mount") is None


def test_generated_component_placeable_on_pcb(cat):
    from cadbuildr.electronics import PCB

    pcb = PCB(40, 30)
    before = len(pcb.board.operations)
    pcb.place(cat.build_part("NE555P"), "U1", 0, 0)  # DIP-8 → drills 8 holes
    assert len(pcb.board.operations) > before
    assert isinstance(pcb.to_dag(), dict)
