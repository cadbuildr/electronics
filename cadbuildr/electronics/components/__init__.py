"""The component catalogue: individual PCB parts, each carrying its footprint."""

from .passives import (
    Resistor,
    ResistorSMD,
    CeramicCapacitor,
    ElectrolyticCapacitor,
)
from .diodes import LED, Diode
from .connectors import (
    PinHeader,
    ScrewTerminal,
    USBTypeA,
    USBMicroB,
    RJ45,
    BarrelJack,
)
from .ics import DIP, SOIC, QFP
from .misc import Crystal, TactileButton

__all__ = [
    # passives
    "Resistor",
    "ResistorSMD",
    "CeramicCapacitor",
    "ElectrolyticCapacitor",
    # diodes
    "LED",
    "Diode",
    # connectors
    "PinHeader",
    "ScrewTerminal",
    "USBTypeA",
    "USBMicroB",
    "RJ45",
    "BarrelJack",
    # ICs
    "DIP",
    "SOIC",
    "QFP",
    # misc
    "Crystal",
    "TactileButton",
]
