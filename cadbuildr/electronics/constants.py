"""Shared constants for the PCB component library.

Everything is in millimetres. The ``0.1"`` (2.54 mm) grid is the de-facto
standard pitch for through-hole parts, so most footprints are expressed as
multiples of it.
"""

from __future__ import annotations

from dataclasses import dataclass

# --- Grid / units -----------------------------------------------------------

INCH = 25.4
THOU = INCH / 1000.0  # 1 mil
PITCH_100 = 0.1 * INCH  # 2.54 mm — the classic header / DIP pitch
PITCH_050 = 0.05 * INCH  # 1.27 mm — fine-pitch headers
DIP_ROW_SPACING = 0.3 * INCH  # 7.62 mm — standard narrow-DIP row spacing

# --- Board defaults ---------------------------------------------------------

DEFAULT_BOARD_THICKNESS = 1.6  # the ubiquitous FR-4 thickness
DEFAULT_COPPER_THICKNESS = 0.035  # 1 oz copper (used only for visual pads)


@dataclass(frozen=True)
class Colors:
    """Brand-ish palette so boards read clearly in the viewer."""

    board_green: str = "#0b6b3a"
    board_blue: str = "#1b3a6b"
    board_black: str = "#1b1b1b"
    board_red: str = "#8b1a1a"
    copper: str = "#c87533"
    gold: str = "#d4af37"
    silver: str = "#c0c0c0"
    tin: str = "#9aa0a6"
    plastic_black: str = "#161616"
    plastic_blue: str = "#243b6b"
    ceramic_tan: str = "#caa46a"
    resistor_beige: str = "#d8c8a0"
    led_red: str = "#d11a1a"
    led_green: str = "#1ca81c"
    led_yellow: str = "#e8c000"
    led_blue: str = "#1666d0"
    ic_black: str = "#202020"
    metal_shell: str = "#b8bcc2"


COLORS = Colors()

# Map a friendly board-color name to a hex value.
BOARD_COLOR_CHOICES: dict[str, str] = {
    "green": COLORS.board_green,
    "blue": COLORS.board_blue,
    "black": COLORS.board_black,
    "red": COLORS.board_red,
}

LED_COLOR_CHOICES: dict[str, str] = {
    "red": COLORS.led_red,
    "green": COLORS.led_green,
    "yellow": COLORS.led_yellow,
    "blue": COLORS.led_blue,
}
