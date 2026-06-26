"""Parametric ``@cadbuildr_project`` entry points for the PCB demo.

Each function wraps a board / assembly with a typed parameter schema consumed by
the SDK auto-form and the github-io Pyodide demo.
"""

from __future__ import annotations

from cadbuildr.foundation import Color, Enum, Int, cadbuildr_project

from .pcb import PCB
from .components import LED, PinHeader, Resistor
from .boards import ArduinoUno, RaspberryPi  # noqa: F401  (re-exported convenience)

BOARD_COLOR_CHOICES = ("green", "blue", "black", "red")
LED_COLORS = ("red", "green", "yellow", "blue")


@cadbuildr_project(
    project_id="pcb_header_strip",
    title="Pin-header strip",
    description="A bare board carrying a single configurable pin header — the "
    "smallest end-to-end demo of the footprint dual-action.",
    parameters=[
        Int("positions", default=8, min=1, max=40, step=1, label="Positions"),
        Int("rows", default=1, min=1, max=2, step=1, label="Rows"),
        Color("board_color", default="green", choices=BOARD_COLOR_CHOICES, label="Board color"),
    ],
)
def header_strip(positions: int, rows: int, board_color: str) -> PCB:
    width = max(20.0, positions * 2.54 + 8.0)
    pcb = PCB(width, 16.0, color=board_color)
    pcb.place(PinHeader(positions=positions, rows=rows), ref="J1", x=0.0, y=0.0)
    return pcb


@cadbuildr_project(
    project_id="pcb_blinky",
    title="Blinky board",
    description="A tiny board: header, current-limit resistor and an LED — the "
    "canonical 'hello world' of electronics.",
    parameters=[
        Color("led_color", default="red", choices=LED_COLORS, label="LED color"),
        Color("board_color", default="blue", choices=BOARD_COLOR_CHOICES, label="Board color"),
        Int("resistor_ohms", default=220, min=100, max=1000, step=10, label="Resistor (Ω)"),
    ],
)
def blinky(led_color: str, board_color: str, resistor_ohms: int) -> PCB:
    pcb = PCB(50.0, 24.0, color=board_color)
    pcb.place(PinHeader(positions=2), ref="J1", x=-20.0, y=0.0)
    pcb.place(Resistor(str(resistor_ohms)), ref="R1", x=-2.0, y=0.0)
    pcb.place(LED(led_color), ref="D1", x=18.0, y=0.0)
    return pcb


@cadbuildr_project(
    project_id="pcb_demo_board",
    title="Reference board",
    description="Pick a well-known open-hardware board reproduced from the "
    "component library (Arduino Uno or Raspberry Pi).",
    parameters=[
        Enum(
            "board",
            default="arduino_uno",
            choices=("arduino_uno", "raspberry_pi"),
            label="Board",
        ),
    ],
)
def demo_board(board: str) -> PCB:
    if board == "raspberry_pi":
        return RaspberryPi()
    return ArduinoUno()


__all__ = ["header_strip", "blinky", "demo_board"]
