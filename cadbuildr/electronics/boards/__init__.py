"""Reference board assemblies that validate the library by reproducing the look
of well-known open-hardware boards."""

from .arduino_uno import ArduinoUno
from .arduino_nano import ArduinoNano
from .raspberry_pi import RaspberryPi
from .raspberry_pi_pico import RaspberryPiPico
from .esp32_devkit import ESP32DevKit

__all__ = [
    "ArduinoUno",
    "ArduinoNano",
    "RaspberryPi",
    "RaspberryPiPico",
    "ESP32DevKit",
]
