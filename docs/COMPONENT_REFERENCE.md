# PCB Component Reference

A sourcing guide for the parts in this library: the **standard names** each
maps to (KiCad / JEDEC / IPC), **canonical dimensions** (from datasheets and
standards), and **where to get authoritative 3D models** — with licensing
notes so we only pull from sources we're allowed to.

> **Workflow we follow** (see licensing below for *why*): code the parametric
> bodies from **datasheet dimensions** (facts, not copyrightable), name the
> land patterns after the **KiCad** footprint libraries, and use KiCad's
> `kicad-packages3d` STEP/VRML models only as a *visual cross-check*, not by
> copying files in.

---

## 1. Naming map — our class → standard names

| Our class | KiCad footprint family | JEDEC / standard | Notes |
|---|---|---|---|
| `Resistor` (axial THT) | `Resistor_THT:R_Axial_DIN0207` (and DIN0204…) | — | lead pitch = body series (0.4" common for ¼ W) |
| `ResistorSMD` | `Resistor_SMD:R_0805_2012Metric` (0402/0603/1206 too) | IPC-7351 `RESC2012X…` | metric body code = exact mm size |
| `CeramicCapacitor` | `Capacitor_THT:C_Disc_D…_P2.54mm` | — | radial disc / MLCC |
| `ElectrolyticCapacitor` | `Capacitor_THT:CP_Radial_D6.3mm_P2.50mm` | — | aluminium can, polarised |
| `LED` (3/5 mm THT) | `LED_THT:LED_D5.0mm` / `LED_D3.0mm` | T-1¾ / T-1 | 0.1" lead pitch |
| `Diode` (axial) | `Diode_THT:D_DO-35_SOD27…` / `D_DO-41…` | DO-204AH / DO-204AL | glass (DO-35) vs plastic (DO-41) |
| `PinHeader` | `Connector_PinHeader_2.54mm:PinHeader_1x0N_P2.54mm…` | — | 0.64 mm sq posts, 2.54 mm pitch |
| `ScrewTerminal` | `TerminalBlock_Phoenix:…_P5.08mm` | — | 5.08 mm pitch typical |
| `USBTypeA` | `Connector_USB:USB_A_…_Horizontal` | — | THT host receptacle |
| `USBMicroB` | `Connector_USB:USB_Micro-B_…` | — | 5 SMD + 2 shield THT |
| `RJ45` | `Connector_RJ:RJ45_…` | 8P8C | shielded jack |
| `BarrelJack` | `Connector_BarrelJack:BarrelJack_Horizontal` | — | 2.1 mm centre pin |
| `DIP` | `Package_DIP:DIP-N_W7.62mm` / `W15.24mm` | JEDEC MS-001 | 0.3"/0.6" row spacing |
| `SOIC` | `Package_SO:SOIC-N_…_P1.27mm` | MS-012 (narrow) / MS-013 (wide) | 1.27 mm pitch |
| `QFP` | `Package_QFP:LQFP-N_…` | MS-026 | 0.4–0.8 mm pitch |
| `Crystal` | `Crystal:Crystal_HC49-U_Vertical` / `HC49-4H…` | — | quartz can |
| `TactileButton` | `Button_Switch_THT:SW_PUSH_6mm` | — | 4-leg 6 mm tactile |

KiCad footprint libraries (authoritative, GitLab):
<https://gitlab.com/kicad/libraries/kicad-footprints>,
3D models <https://gitlab.com/kicad/libraries/kicad-packages3d>.

---

## 2. Canonical dimensions (mm)

All values are datasheet / standard figures; "BSC" = basic spacing (exact, no
tolerance). These are the numbers coded into `constants.py` and the component
classes.

### Chip resistors / capacitors (two-terminal SMD)

| Imperial | Metric | L | W | H (resistor, typ.) | IPC-7351 land (gap G / span Z) |
|---|---|---|---|---|---|
| 0402 | 1005 | 1.00 | 0.50 | 0.35 | 0.50 / 1.60 |
| 0603 | 1608 | 1.60 | 0.80 | 0.45–0.55 | 0.80 / 2.40 |
| 0805 | 2012 | 2.00 | 1.25 | 0.50–0.55 | 1.00 / 2.80 |
| 1206 | 3216 | 3.20 | 1.60 | 0.55 | 1.75 / 4.05 |

Capacitor heights are **not** fixed by the size code — take per part.

### Through-hole staples

| Part | Key dimensions |
|---|---|
| 0.1" pin header | pitch 2.54 mm; posts 0.64 mm sq; pin len 6.0 mm above / 3.0 below; drill 0.9–1.0 mm |
| DIP (MS-001) | pitch 2.54 mm; rows 7.62 mm (300 mil) or 15.24 mm (600 mil); lead ~0.46 mm; drill 0.8–1.0 mm |
| 5 mm LED | lens Ø5.0; flange Ø~5.8; height ~8.6; pitch 2.54 mm; drill 0.8 mm |
| 3 mm LED | lens Ø3.0; flange Ø~3.8; panel hole 3.2 mm |
| HC-49/U crystal | body 11.05 × 4.65; height ~13.5 (US low-profile ~3.5–4.5); lead spacing 4.88 mm; lead Ø0.43 |
| DO-35 (1N4148) | body 3.0–4.0 × Ø2.0; lead Ø0.5 |
| DO-41 (1N4007) | body 4.1–5.2 × Ø2.0–2.7; lead Ø0.8 |
| TO-92 | body ~4.5–5.2 wide × 3.7–4.2 deep; molded pitch 1.27 (splayed to 2.54) |
| TO-220 | body 10.16 wide × ~4.5 thick; tab hole Ø3.6–3.8; pitch 2.54 |

### SOIC (MS-012/013), 1.27 mm pitch BSC

| Variant | Body width | Lead span (tip-tip) | Height |
|---|---|---|---|
| Narrow (150 mil) | 3.90 BSC | 6.00 BSC | 1.35–1.75 |
| Wide (300 mil) | 7.50 BSC | 10.30 BSC | 2.35–2.65 |

Body length grows ~1.27 mm per lead pair (SOIC) / ~2.54 mm per pair (DIP).

### SOT-23 (TO-236 / MO-178)

pitch 0.95 mm (same-side 1.90); body 2.9 × 1.3; span ~2.4; height ~1.0.

**Standards:** JEDEC **JEP95** registered outlines (MS-/MO- numbers);
**IPC-7351B** land patterns with density levels **Most/Nominal/Least** (suffix
M/N/L) and the `RESC/CAPC/SOIC/QFP…` naming convention; **IPC-2221** for the
generic PCB design rules (clearances, hole sizing).

---

## 3. Where to get 3D models / footprints — and what we may reuse

**Bottom line:** for an open-source (MIT/Apache) repo, the only source you can
**redistribute model files** from is **KiCad's official libraries**. Every
other portal grants a "use it in *your* board design" license, **not** a
"republish the model in a public library" license. So we **derive dimensions
from datasheets** (facts aren't copyrightable) and generate our own geometry.

| Source | What you get | Format | Reuse verdict |
|---|---|---|---|
| **KiCad libraries** (gitlab.com/kicad) | symbols, footprints, 3D | `.kicad_mod`, `.step`, `.wrl` | ✅ **Redistributable** under CC-BY-SA 4.0 **+ KiCad Library Exception** (attribution; keep library assets segregated from MIT/Apache code) |
| **SnapEDA / SnapMagic** | sym/fp/3D | STEP | ⚠️ use in *your* board only — CAD files stay CC-BY-SA; do **not** bundle |
| **Ultra Librarian** (Cadence/EMA) | sym/fp/3D | STEP | ❌ EULA, no redistribution, ownership retained |
| **SamacSys / ComponentSearchEngine** | sym/fp/3D | STEP | ❌ use-in-design only |
| **Digi-Key / Mouser CAD** | sym/fp/3D | STEP | ❌ inherit SnapEDA / SamacSys terms |
| **3DContentCentral** (Dassault) | 3D | STEP/native | ❌ design-use only, mixed provenance |
| **GrabCAD** | 3D | STEP/STL/native | ❌ non-commercial, per-model permission, often unlicensed |
| **Manufacturer datasheets** | dimensioned drawings | PDF | ✅ **dimensions are facts** — redraw geometry from them; don't copy the drawing artwork |

Licensing references: KiCad <https://www.kicad.org/libraries/license/>;
SnapEDA FAQ <https://www.snapeda.com/about/FAQ/>; Ultra Librarian legal
<https://www.ultralibrarian.com/legal>; GrabCAD terms
<https://grabcad.com/terms>.

### Recommendation

1. **Primary:** generate bodies + land patterns parametrically from datasheet
   dimensions (this library). Clean MIT/Apache ownership of the output.
2. **If bundling pre-made models:** only KiCad `kicad-packages3d`, kept under a
   clearly-marked `LICENSE.libraries` (CC-BY-SA + exception) separate from code.
3. **Never** bundle files from SnapEDA, Ultra Librarian, SamacSys, Digi-Key /
   Mouser, 3DContentCentral, or GrabCAD.

Datasheet anchors used for the dimension tables above: Vishay D/CRCW
(resistors), Analog Devices R-8 (SOIC), Microchip 1N4148 (DO-35), Nexperia
SOT23, Abracon/Farnell HC-49, JEDEC JEP95 master index, IPC-7351B naming PDF.
