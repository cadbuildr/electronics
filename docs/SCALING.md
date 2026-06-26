# Scaling to catalog size

How this library grows from a few hand-written parts to **Digi-Key-scale**
without becoming thousands of classes.

## The thesis (validated against Digi-Key)

Digi-Key lists **~18 million part numbers**, but those collapse onto only
**~15,000 standard footprints** (the entire KiCad library) which themselves
come from **a few dozen package families**. That's a **~1000:1 collapse**, and
the reason is simple:

> **Geometry is a pure function of `Package/Case` + `Mounting Type` + pin count
> + pitch — never the electrical value.** A 1 kΩ and a 10 kΩ 0805 resistor are
> the *same* land pattern and the *same* 3D body. Thousands of unrelated ICs
> share `SOIC-8`.

So we never write 12,000 classes. We write a handful of **generators**, a few
hundred **package** rows, and let **parts** be thin data.

## Three layers

```
 K family generators   ◀──  M package instances  ◀──  N parts
   (~a dozen, code)          (hundreds, data)           (thousands+, data)
   families/                 data/packages.json         data/parts.csv
```

| Layer | What it is | Where | How many | To add one |
|---|---|---|---|---|
| **Family** | a parametric generator: `dims → (3D body, IPC land pattern)` | `families/generators.py` | ~a dozen | write a `PackageFamily` subclass + `register()` |
| **Package** | one bounded geometry: family + dims + IPC/KiCad/JEDEC names | `data/packages.json` | hundreds | add a JSON row |
| **Part** | an MPN + a package ref + electrical/cosmetic attrs | `data/parts.csv` | unbounded | add a CSV row |

`N` parts → `M` packages → `K` generators, with `M ≪ N` and `K` tiny. This is
exactly KiCad's footprint-generator model (one Python generator + a YAML size
table → hundreds of `.kicad_mod` files), unified so **one dimension set drives
both the footprint and the 3D body** (KiCad keeps them in separate repos; we
don't).

## Using it

```python
from cadbuildr.electronics import Catalog, PCB

cat = Catalog.load()                       # data/packages.json + data/parts.csv
u1 = cat.build_part("ATMEGA328P-AU")       # MPN → TQFP-32 geometry
pcb = PCB(40, 30)
pcb.place(u1, "U1", 0, 0)                   # same dual-action place() as everything else
```

Add a brand-new part with **zero code** — one row in `data/parts.csv`:

```csv
mpn,manufacturer,category,package,value,tolerance,color
RC0603FR-071KL,Yageo,Resistor,R_0603,1k,1%,
```

Add a new package (a size not yet in the table) — one row in
`data/packages.json`:

```json
"SOIC-20": {"family": "gullwing_dual", "ipc_name": "SOIC127P600X175-20N",
  "kicad_fp": "Package_SO:SOIC-20_...", "jedec": "MS-013",
  "dims": {"pins": 20, "pitch": 1.27, "lead_span": 10.3, "lead_len": 0.8,
           "lead_w": 0.42, "body_l": 12.8, "body_w": 7.5, "body_h": 2.35}}
```

## Ingesting from Digi-Key

You can't legally cache Digi-Key's attribute *data* (their API User Agreement
forbids building a database from it), and their CAD models are licensed for
use-in-design only (not redistributable). But the **string format** of the
`Package / Case` field is just a schema, and **dimensions are facts**. So the
scalable, license-clean path is: read a part's `Package / Case` + `Mounting
Type`, map it to one of our packages, and **generate** the geometry.

```python
cat.resolve_package_case("0805 (2012 Metric)", mounting="Surface Mount")  # → R_0805
cat.resolve_package_case('8-DIP (0.300", 7.62mm)', mounting="Through Hole")  # → DIP-8
```

`catalog/digikey.py` handles Digi-Key's real-world string quirks (imperial +
`(metric Metric)` for passives, `8-SOIC (…)` lead-count prefixes, comma-joined
aliases like `TO-236-3, SC-59, SOT-23-3`, `DO-214AC, SMA` punctuation drift).

## Where the geometry comes from — IPC-7351B

Land patterns are generated from package lead geometry + the IPC-7351B fillet
goals (toe `Jt`, heel `Jh`, side `Js`) at the Nominal (N) density level
(`families/_ipc.py`), so they follow the same standard the real footprint
libraries do:

```
Z = lead_span + 2·Jt        G = (lead_span − 2·lead_len) − 2·Jh
pad_len = (Z − G)/2         pad_offset = (Z + G)/4        pad_wid = lead_w + 2·Js
```

Through-hole families use the IPC-7251 rule `hole = lead Ø + clearance`, pad =
`hole + 2·(ring + fab)`. We use single nominal dimensions and drop the RMS
tolerance term (fine for a mechanical/visual library); see the limitations note
in `families/_ipc.py`.

## Roadmap to full catalogue scale

The backbone is in place (chip, gull-wing dual, gull-wing quad, DIP families +
a Digi-Key resolver). To reach Digi-Key breadth:

1. **More families** — `nolead` (QFN/DFN), `sot`/`to` (transistors, regulators),
   `bga`, and the connector families. The geometry surface stays ~15–20
   generators.
2. **Fill the package table** — the ~hundreds of standard `Package/Case` values
   (one JSON row each), cross-referenced to KiCad/JEDEC names. Pull exact
   dimensions from JEDEC JEP95 outlines + datasheets (facts, redistributable).
3. **3D leads on SMD bodies** — add gull-wing/J-lead geometry to the generated
   bodies (currently a body box; pads render as board copper).
4. **Optional live enrichment** — a thin Digi-Key API v4 client (OAuth client
   credentials) to look up a part's `Package/Case` on demand and feed
   `resolve_package_case`, without caching their data.
5. **KiCad cross-check** — compare generated land patterns against
   `kicad-footprints` (the one redistributable source) in CI.

See `docs/COMPONENT_REFERENCE.md` for the standards/dimensions/licensing detail
behind each family.
