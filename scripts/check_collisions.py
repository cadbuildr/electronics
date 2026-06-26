"""Component-collision check for the reference boards.

Renders each board through a kernel-api ``/render`` endpoint, reconstructs every
component's world-space bounding box from the returned mesh, and reports any
pair of component bodies that physically overlap (a real placement bug — two
parts occupying the same space). Exits non-zero if any board has a collision, so
it can gate CI / a pre-commit hook.

Usage::

    KERNEL_API_URL=http://localhost:9087 \
      python scripts/check_collisions.py

Defaults to the public kernel-api if ``KERNEL_API_URL`` is unset. A pair counts
as colliding only when its bounding boxes overlap by more than ``PEN`` mm in
*both* X and Y (and any positive Z), so merely-touching leads don't false-trip.
"""

from __future__ import annotations

import json
import os
import sys
import urllib.request

from cadbuildr.foundation.dag_utils import show_dag
from cadbuildr.electronics.boards import (
    ArduinoNano,
    ArduinoUno,
    ESP32DevKit,
    RaspberryPi,
    RaspberryPiPico,
)

BOARDS = [ArduinoUno, ArduinoNano, RaspberryPi, RaspberryPiPico, ESP32DevKit]

KERNEL_URL = os.environ.get("KERNEL_API_URL", "https://kernel-api.cadbuildr.com").rstrip("/")
RENDER_URL = f"{KERNEL_URL}/v1/kernels/replicad/render"
TOKEN = os.environ.get("CADBUILDR_SESSION_TOKEN", "cbv1.dev.local")

PEN = 0.3  # mm penetration in BOTH X and Y to count as a real collision


def _render(dag: dict) -> dict:
    body = json.dumps({"dag": dag, "format": "json", "kernel": "replicad"}).encode()
    req = urllib.request.Request(
        RENDER_URL,
        body,
        {"content-type": "application/json", "authorization": f"Bearer {TOKEN}"},
    )
    return json.loads(urllib.request.urlopen(req, timeout=180).read())


def _world_aabb(verts: list[float], tf: list[float]) -> tuple[float, ...]:
    """World AABB of a mesh: transform every vertex by the (column-major,
    three.js layout) 16-float matrix and take the min/max per axis."""
    m = tf
    lo = [1e9, 1e9, 1e9]
    hi = [-1e9, -1e9, -1e9]
    for i in range(0, len(verts), 3):
        x, y, z = verts[i], verts[i + 1], verts[i + 2]
        w = (
            m[0] * x + m[4] * y + m[8] * z + m[12],
            m[1] * x + m[5] * y + m[9] * z + m[13],
            m[2] * x + m[6] * y + m[10] * z + m[14],
        )
        for a in range(3):
            lo[a] = min(lo[a], w[a])
            hi[a] = max(hi[a], w[a])
    return (lo[0], lo[1], lo[2], hi[0], hi[1], hi[2])


def _overlap(a0: float, a1: float, b0: float, b1: float) -> float:
    return min(a1, b1) - max(a0, b0)


def check_board(name: str, dag: dict) -> int:
    mesh = _render(dag)["mesh"]
    store = mesh["store"]
    comps = []
    for inst in mesh.get("partInstances", []):
        path = inst.get("path") or ""
        if "/components__" not in path:  # board substrate + non-mesh nodes
            continue
        faces = store.get(inst["hash"], {}).get("data", {}).get("faces", {})
        verts = faces.get("vertices") or faces.get("positions") or []
        if not verts:
            continue
        label = path.rsplit("/", 1)[-1].split("__")[0]
        comps.append((label, _world_aabb(verts, inst["tf"])))

    hits = []
    for i in range(len(comps)):
        for j in range(i + 1, len(comps)):
            n1, a = comps[i]
            n2, b = comps[j]
            ox = _overlap(a[0], a[3], b[0], b[3])
            oy = _overlap(a[1], a[4], b[1], b[4])
            oz = _overlap(a[2], a[5], b[2], b[5])
            if ox > PEN and oy > PEN and oz > 0:
                hits.append((n1, n2, round(ox, 2), round(oy, 2), round(oz, 2)))

    status = "OK" if not hits else f"{len(hits)} COLLISION(S)"
    print(f"{name:18s} {len(comps):2d} components  {status}")
    for n1, n2, ox, oy, oz in sorted(hits, key=lambda c: -(c[2] * c[3])):
        print(f"    {n1:24s} x {n2:24s}  overlap = {ox} x {oy} x {oz} mm")
    return len(hits)


def main() -> int:
    print(f"collision check via {RENDER_URL}\n")
    total = sum(check_board(cls.__name__, show_dag(cls())) for cls in BOARDS)
    print(f"\nTotal colliding pairs: {total}")
    return 1 if total else 0


if __name__ == "__main__":
    sys.exit(main())
