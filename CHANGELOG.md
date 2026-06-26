# Changelog

All notable changes to this project are documented in this file.

## 0.1.0 - 2026-06-26

- Initial public release of `cadbuildr.electronics`.
- 3D PCB component library (resistors, capacitors, LEDs, pin headers, USB /
  Ethernet connectors, DIP / SOIC / QFP ICs, crystals, buttons) with a
  footprint-driven `PCB` assembly that drills the board and seats parts in one
  call.
- Reference boards built from the library: Arduino Uno (genuine R3 edge-cut
  outline), Arduino Nano, Raspberry Pi, Raspberry Pi Pico, ESP32 DevKitC —
  reviewed against real layouts and verified collision-free
  (`scripts/check_collisions.py`).
- Components live in a `components` sub-assembly so the viewer can show a bare,
  drilled board and reveal the population via the assembly tree.
- `github-io/` interactive demo (Pyodide + `@cadbuildr/sdk-react`) with a
  GitHub Pages deploy workflow.
