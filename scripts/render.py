#!/usr/bin/env python3
"""Render PCB components and boards to PNG so geometry can be *visually* checked.

Pipeline (no GPU / no display required):

    Python object ──show_dag──▶ DAG ──kernel-api(replicad)──▶ colored mesh
        └──────────────── matplotlib (headless, Agg) ──────────▶ PNG

The kernel-api is the same CAD kernel the web viewer uses. Run it locally with
no auth (see the README "Visual verification" section):

    cd tsjs && PORT=8087 node apps/kernel-api/dist/server.js

then point this script at it (default ``http://localhost:8087`` or
``$CAD_COMPILE_API_BASE_URL``).

Examples
--------
    # one board, three views
    python scripts/render.py --target arduino -o /tmp/arduino.png

    # the whole component gallery
    python scripts/render.py --gallery -o /tmp/pcb_gallery
"""

from __future__ import annotations

import argparse
import os
import sys

import numpy as np
import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt  # noqa: E402

from cadbuildr.foundation import KernelApiClient
from cadbuildr.foundation.dag_utils import show_dag

from cadbuildr.electronics import (
    PCB,
    LED,
    Diode,
    Resistor,
    ResistorSMD,
    CeramicCapacitor,
    ElectrolyticCapacitor,
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
)
from cadbuildr.electronics.boards import ArduinoUno, RaspberryPi


# --- known build targets ----------------------------------------------------

def _blinky() -> PCB:
    pcb = PCB(50, 24, color="blue")
    pcb.place(PinHeader(positions=2), "J1", -20, 0)
    pcb.place(Resistor("220"), "R1", -2, 0)
    pcb.place(LED("red"), "D1", 18, 0)
    return pcb


COMPONENTS = {
    "resistor": lambda: Resistor("220"),
    "resistor_smd": lambda: ResistorSMD("10k", "0805"),
    "capacitor_ceramic": lambda: CeramicCapacitor("100n"),
    "capacitor_electrolytic": lambda: ElectrolyticCapacitor("100u"),
    "led": lambda: LED("red"),
    "diode": lambda: Diode(),
    "pin_header_1x8": lambda: PinHeader(positions=8),
    "pin_header_2x5": lambda: PinHeader(positions=5, rows=2),
    "screw_terminal": lambda: ScrewTerminal(3),
    "usb_a": lambda: USBTypeA(),
    "usb_micro_b": lambda: USBMicroB(),
    "rj45": lambda: RJ45(),
    "barrel_jack": lambda: BarrelJack(),
    "dip28": lambda: DIP(28),
    "soic8": lambda: SOIC(8),
    "qfp32": lambda: QFP(32),
    "crystal": lambda: Crystal(),
    "tactile_button": lambda: TactileButton(),
}

BOARDS = {
    "blinky": _blinky,
    "arduino": ArduinoUno,
    "raspberry": RaspberryPi,
}

TARGETS = {**COMPONENTS, **BOARDS}

VIEWS = [(28, -58, "iso"), (90, -90, "top"), (6, -90, "front")]

# Background and image size for the software rasterizer.
BG = np.array([1.0, 1.0, 1.0])
RASTER_W, RASTER_H = 560, 480


# --- software z-buffer rasterizer (headless, numpy-only) --------------------
#
# matplotlib's 3D has no depth buffer — it paint-sorts whole faces by mean z,
# so a board's two big triangles hide every low component on it. We need real
# per-pixel occlusion, so we rasterize ourselves: orthographic projection +
# barycentric fill + a z-buffer. No GPU, no GL, deterministic.

def _camera_basis(elev_deg: float, azim_deg: float):
    e, a = np.radians(elev_deg), np.radians(azim_deg)
    cam_from_target = np.array([np.cos(e) * np.cos(a), np.cos(e) * np.sin(a), np.sin(e)])
    forward = -cam_from_target  # into the screen
    right = np.cross(forward, [0.0, 0.0, 1.0])
    if np.linalg.norm(right) < 1e-6:
        right = np.array([1.0, 0.0, 0.0])
    right /= np.linalg.norm(right)
    up = np.cross(right, forward)
    up /= np.linalg.norm(up)
    return right, up, forward


def rasterize_view(tris, facecolors, elev, azim, light, w=RASTER_W, h=RASTER_H):
    right, up, forward = _camera_basis(elev, azim)
    verts = tris.reshape(-1, 3)
    sx = verts @ right
    sy = verts @ up
    depth = verts @ forward  # larger = farther

    pad = 0.06
    minx, maxx, miny, maxy = sx.min(), sx.max(), sy.min(), sy.max()
    scale = min(w * (1 - 2 * pad) / (maxx - minx + 1e-9),
                h * (1 - 2 * pad) / (maxy - miny + 1e-9))
    px = (sx - minx) * scale + (w - (maxx - minx) * scale) / 2
    py = h - ((sy - miny) * scale + (h - (maxy - miny) * scale) / 2)
    px = px.reshape(-1, 3)
    py = py.reshape(-1, 3)
    pz = depth.reshape(-1, 3)

    # Flat shading from face normal.
    e1 = tris[:, 1] - tris[:, 0]
    e2 = tris[:, 2] - tris[:, 0]
    nrm = np.cross(e1, e2)
    ln = np.linalg.norm(nrm, axis=1, keepdims=True)
    ln[ln == 0] = 1.0
    nrm /= ln
    shade = np.clip(np.abs(nrm @ light), 0, 1) * 0.72 + 0.28
    colors = np.clip(facecolors * shade[:, None], 0, 1)

    img = np.ones((h, w, 3)) * BG
    zbuf = np.full((h, w), np.inf)

    for i in range(len(tris)):
        x0, x1, x2 = px[i]
        y0, y1, y2 = py[i]
        area = (x1 - x0) * (y2 - y0) - (x2 - x0) * (y1 - y0)
        if abs(area) < 1e-9:
            continue
        xmin = max(int(np.floor(min(x0, x1, x2))), 0)
        xmax = min(int(np.ceil(max(x0, x1, x2))), w - 1)
        ymin = max(int(np.floor(min(y0, y1, y2))), 0)
        ymax = min(int(np.ceil(max(y0, y1, y2))), h - 1)
        if xmin > xmax or ymin > ymax:
            continue
        xs = np.arange(xmin, xmax + 1)
        ys = np.arange(ymin, ymax + 1)
        gx, gy = np.meshgrid(xs + 0.5, ys + 0.5)
        w0 = ((x1 - x0) * (gy - y0) - (y1 - y0) * (gx - x0)) / area
        w1 = ((x2 - x1) * (gy - y1) - (y2 - y1) * (gx - x1)) / area
        w2 = 1.0 - w0 - w1
        inside = (w0 >= 0) & (w1 >= 0) & (w2 >= 0)
        if not inside.any():
            continue
        # barycentric: point = w2*v0 + w0*v2? keep consistent weights for depth
        zd = w2 * pz[i, 0] + w0 * pz[i, 2] + w1 * pz[i, 1]
        sub_z = zbuf[ymin:ymax + 1, xmin:xmax + 1]
        sub_img = img[ymin:ymax + 1, xmin:xmax + 1]
        write = inside & (zd < sub_z)
        sub_z[write] = zd[write]
        sub_img[write] = colors[i]
    return img


# --- mesh assembly ----------------------------------------------------------

def _mat(tf16: list[float]) -> np.ndarray:
    """kernel-api transforms are 16 floats, row-major, row-vector convention:
    the translation lives in the *bottom row*, so a world point is
    ``[x, y, z, 1] @ M`` (no transpose)."""
    return np.array(tf16, dtype=float).reshape(4, 4)


def fetch_colored_triangles(client: KernelApiClient, obj, kernel: str):
    """Return (tris Nx3x3, facecolors Nx3) for every placed instance, with
    each instance's paint colour and placement transform applied."""
    mesh = client.compile_mesh(dag=show_dag(obj), kernel=kernel)["mesh"]
    store = mesh["store"]
    instances = mesh["partInstances"]

    tris_all, cols_all = [], []
    for inst in instances:
        geom = store[inst["geometryKey"]]
        faces = geom["data"]["faces"]
        verts = np.array(faces["vertices"], dtype=float).reshape(-1, 3)
        idx = np.array(faces["triangles"], dtype=int).reshape(-1, 3)
        color = geom["data"].get("color") or [0.6, 0.6, 0.6]

        m = _mat(inst.get("tf") or list(np.eye(4).flatten()))
        homog = np.hstack([verts, np.ones((len(verts), 1))])
        world = (homog @ m)[:, :3]

        tris = world[idx]  # (T, 3, 3)
        tris_all.append(tris)
        cols_all.append(np.tile(color, (len(tris), 1)))

    if not tris_all:
        raise RuntimeError("mesh had no part instances")
    return np.concatenate(tris_all), np.concatenate(cols_all)


def render_png(tris: np.ndarray, base_colors: np.ndarray, out: str, title: str):
    """Rasterize each view with a real z-buffer and save a multi-view PNG."""
    light = np.array([0.35, 0.45, 0.82])
    light /= np.linalg.norm(light)

    fig = plt.figure(figsize=(4.6 * len(VIEWS), 4.6), dpi=120)
    fig.suptitle(title, fontsize=13)
    for k, (elev, azim, name) in enumerate(VIEWS):
        img = rasterize_view(tris, base_colors, elev, azim, light)
        ax = fig.add_subplot(1, len(VIEWS), k + 1)
        ax.imshow(img, interpolation="nearest")
        ax.set_axis_off()
        ax.set_title(name, fontsize=10)
    fig.tight_layout(rect=(0, 0, 1, 0.95))
    fig.savefig(out, bbox_inches="tight", facecolor="white")
    plt.close(fig)


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--target", choices=sorted(TARGETS), help="component or board to render")
    ap.add_argument("--part", help="catalog part MPN to render (data-driven), e.g. NE555P")
    ap.add_argument("--gallery", action="store_true", help="render every component + board")
    ap.add_argument("-o", "--out", required=True, help="output PNG (or dir with --gallery)")
    ap.add_argument(
        "--base-url",
        default=os.getenv("CAD_COMPILE_API_BASE_URL", "http://localhost:8087"),
        help="kernel-api base url",
    )
    ap.add_argument("--kernel", default="replicad", choices=["replicad", "truck"])
    args = ap.parse_args()

    client = KernelApiClient(base_url=args.base_url, timeout_s=300)
    try:
        client.health()
    except Exception as exc:  # noqa: BLE001
        print(
            f"kernel-api not reachable at {args.base_url}: {exc}\n"
            "Start it: cd tsjs && PORT=8087 node apps/kernel-api/dist/server.js",
            file=sys.stderr,
        )
        return 2

    if args.gallery:
        os.makedirs(args.out, exist_ok=True)
        failures = 0
        for name, factory in TARGETS.items():
            try:
                tris, cols = fetch_colored_triangles(client, factory(), args.kernel)
                render_png(tris, cols, os.path.join(args.out, f"{name}.png"), name)
                print(f"  {name:24s} {len(tris):6d} tris")
            except Exception as exc:  # noqa: BLE001
                failures += 1
                print(f"  {name:24s} FAILED {exc!r}", file=sys.stderr)
        print(f"gallery -> {args.out} ({failures} failures)")
        return 1 if failures else 0

    if args.part:
        from cadbuildr.electronics.catalog import Catalog

        comp = Catalog.load().build_part(args.part)
        tris, cols = fetch_colored_triangles(client, comp, args.kernel)
        render_png(tris, cols, args.out, args.part)
        print(f"{args.part} -> {args.out} ({len(tris)} tris)")
        return 0

    if not args.target:
        ap.error("pass --target NAME, --part MPN, or --gallery")
    tris, cols = fetch_colored_triangles(client, TARGETS[args.target](), args.kernel)
    render_png(tris, cols, args.out, args.target)
    print(f"{args.target} -> {args.out} ({len(tris)} tris)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
