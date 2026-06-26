# Visual verification

How to actually *look* at the geometry this library builds — render any
component or board to a PNG and eyeball it. No GPU, no display, no cloud auth.

```
Python object ──show_dag──▶ DAG ──kernel-api (replicad/WASM)──▶ colored mesh
     └──────────── numpy z-buffer rasterizer (headless) ───────────▶ PNG
```

The renderer (`scripts/render.py`) talks to the **same CAD kernel the web
viewer uses** — `kernel-api` — gets a colored triangle mesh, then rasterizes it
itself (orthographic projection + a real z-buffer, so low components are never
hidden by the board).

## 1. Point at a kernel-api

Any `kernel-api` endpoint works. Use the hosted one
(`https://kernel-api.cadbuildr.com`, the default) or run your own and set
`$CAD_COMPILE_API_BASE_URL` (or `--base-url`). A self-hosted kernel-api needs no
auth when `KERNEL_API_TOKEN` / `CLOUD_AGENT_API_TOKEN` are unset.

## 2. Render

```bash
pip install numpy matplotlib   # the only extra deps the renderer needs

# one target, three views (iso / top / front)
python scripts/render.py --target arduino -o /tmp/arduino.png
python scripts/render.py --target led     -o /tmp/led.png

# the whole catalogue at once
python scripts/render.py --gallery -o /tmp/pcb_gallery
```

`--target` accepts any component (`resistor`, `led`, `dip28`, `rj45`, …) or
board (`blinky`, `arduino`, `raspberry`). Point at a different kernel with
`--base-url` / `$CAD_COMPILE_API_BASE_URL`, or use `--kernel truck`.

## How it works

- `show_dag(obj)` produces the wrapped DAG the kernel expects
  (`{version, rootNodeId, DAG, serializableNodes}` — note: **not** the raw
  `to_dag()` dict).
- `KernelApiClient.compile_mesh(...)` returns `mesh.store` (per-geometry
  triangles + paint color) and `mesh.partInstances` (each with a 4×4 transform,
  **row-major, translation in the bottom row** → world = `[x,y,z,1] @ M`).
- The rasterizer projects every instance's triangles, shades by face normal,
  and z-buffers them into an image. Pure numpy, deterministic, ~1–2 s a frame.

## Known limitations

- **One color per `Part`.** The kernel paints a merged solid a single color
  (the last `paint()` wins), so multi-material parts show their dominant body
  color, not per-feature colors.
- **Identical-shape parts share a color.** Two LEDs of the same geometry but
  different `paint()` dedupe to one geometry hash, so the second reuses the
  first's color. Cosmetic only — placement and shape are unaffected.
- matplotlib only lays the three view panels out; all 3D is the numpy
  rasterizer (matplotlib's own 3D has no depth buffer and hides components).

## Reference renders

Checked-in snapshots live in [`gallery/`](gallery/):

- [`components.png`](gallery/components.png) — every component, iso view
- [`arduino_uno.png`](gallery/arduino_uno.png), [`raspberry_pi.png`](gallery/raspberry_pi.png), [`blinky.png`](gallery/blinky.png)
