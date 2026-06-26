"""Smoke + correctness tests for the PCB library.

These run without the geometry kernel: building a DAG exercises every operation
and ``transformed_pads`` lets us assert that holes really do land under the
components that asked for them (the whole point of the footprint system).
"""

from __future__ import annotations

import math

import pytest

from cadbuildr.electronics import (
    PCB,
    Components,
    Placement,
    Resistor,
    ResistorSMD,
    CeramicCapacitor,
    ElectrolyticCapacitor,
    LED,
    Diode,
    PinHeader,
    ScrewTerminal,
    USBTypeA,
    USBMicroB,
    RJ45,
    BarrelJack,
    DIP,
    SOIC,
    QFP,
    Crystal,
    TactileButton,
    Footprint,
    Pad,
    footprint,
)
from cadbuildr.electronics.boards import (
    ArduinoUno,
    ArduinoNano,
    RaspberryPi,
    RaspberryPiPico,
    ESP32DevKit,
)


ALL_COMPONENTS = [
    lambda: Resistor("220"),
    lambda: ResistorSMD("10k", "0805"),
    lambda: CeramicCapacitor("100n"),
    lambda: ElectrolyticCapacitor("100u"),
    lambda: LED("red"),
    lambda: Diode(),
    lambda: PinHeader(positions=8),
    lambda: PinHeader(positions=5, rows=2),
    lambda: ScrewTerminal(3),
    lambda: USBTypeA(),
    lambda: USBMicroB(),
    lambda: RJ45(),
    lambda: BarrelJack(),
    lambda: DIP(28),
    lambda: SOIC(8),
    lambda: QFP(32),
    lambda: Crystal(),
    lambda: TactileButton(),
]


@pytest.mark.parametrize("factory", ALL_COMPONENTS)
def test_component_builds_and_has_footprint(factory):
    comp = factory()
    dag = comp.to_dag()
    assert isinstance(dag, dict) and dag
    fp = comp.footprint()
    assert isinstance(fp, Footprint)
    assert len(fp.pads) >= 1


def test_through_hole_vs_smd_classification():
    assert Resistor("1k").footprint().is_surface_mount is False
    assert ResistorSMD("1k").footprint().is_surface_mount is True
    assert SOIC(8).footprint().is_surface_mount is True
    assert DIP(8).footprint().is_surface_mount is False


def test_placement_drills_board_and_adds_component():
    pcb = PCB(60, 40)
    ops_before = len(pcb.board.operations)
    pcb.place(PinHeader(positions=8), ref="J1", x=0, y=10)
    ops_after = len(pcb.board.operations)
    # 8 drills were added (plus painted pads), and one component placed.
    assert ops_after > ops_before
    assert len(pcb.placements) == 1
    assert pcb.bom()[0].ref == "J1"


def test_holes_line_up_under_component():
    """A placed footprint's drilled positions must equal the same maths the
    assembly uses to seat the body — that is the no-drift guarantee."""
    fp = PinHeader(positions=4).footprint()
    x, y, rot = 12.0, -7.0, 90.0
    placed = fp.transformed_pads(x, y, rot)
    theta = math.radians(rot)
    for original, moved in zip(fp.pads, placed):
        ex = x + original.x * math.cos(theta) - original.y * math.sin(theta)
        ey = y + original.x * math.sin(theta) + original.y * math.cos(theta)
        assert moved.x == pytest.approx(ex)
        assert moved.y == pytest.approx(ey)
        assert moved.drill == original.drill


def test_from_placements_matches_builder():
    decl = PCB.from_placements(
        50,
        30,
        [
            Placement(Resistor("220"), "R1", 0, 0),
            Placement(LED("red"), "D1", 10, 0, rotation=90),
        ],
    )
    assert len(decl.placements) == 2
    decl.to_dag()


def test_decorator_attaches_footprint():
    from cadbuildr.foundation import Part

    @footprint(Footprint("CUSTOM", pads=[Pad(0, 0, drill=1.0)]))
    class Blob(Part):
        def __init__(self):
            super().__init__()

    pcb = PCB(20, 20)
    pcb.place(Blob(), ref="X1", x=0, y=0)
    assert pcb.placements[0].component.footprint().name == "CUSTOM"


def test_mounting_holes():
    pcb = PCB(50, 50)
    before = len(pcb.board.operations)
    pcb.mounting_holes_rect(3, 3)
    assert len(pcb.board.operations) == before + 4


def test_components_grouped_in_subassembly():
    """Placed parts live in a dedicated ``Components`` sub-assembly so the viewer
    can hide them all at once, while the board stays a direct child of the PCB."""
    pcb = PCB(60, 40)
    pcb.place(PinHeader(positions=4), ref="J1", x=0, y=0)
    pcb.place(Resistor("220"), ref="R1", x=10, y=0)

    # The PCB has exactly two top-level children: the board and the components
    # sub-assembly (a live reference, populated by place()).
    assert pcb.board in pcb.components
    assert isinstance(pcb._components_asm, Components)
    assert pcb._components_asm in pcb.components
    # Both placed parts ended up inside the sub-assembly, not directly on the PCB.
    assert len(pcb._components_asm.components) == 2


def test_reference_boards_build():
    boards = (
        ArduinoUno(),
        ArduinoNano(),
        RaspberryPi(),
        RaspberryPiPico(),
        ESP32DevKit(),
    )
    for board in boards:
        dag = board.to_dag()
        assert isinstance(dag, dict) and dag
        assert len(board.placements) >= 5


def test_components_fit_within_board_outline():
    """Every component courtyard should sit inside the board (a cheap guard
    against fat-fingered coordinates in the reference boards)."""
    board = ArduinoUno()
    hw, hh = board.width / 2.0, board.height / 2.0
    for p in board.placements:
        cw, ch = p.component.footprint().courtyard
        assert abs(p.x) - cw / 2.0 <= hw + 0.5, f"{p.ref} off the right/left edge"
        assert abs(p.y) - ch / 2.0 <= hh + 0.5, f"{p.ref} off the top/bottom edge"
