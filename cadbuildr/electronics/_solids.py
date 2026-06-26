"""Tiny geometry helpers shared by the component bodies.

Everything is expressed in the component's *local* frame: the board top sits at
``z = 0`` and the body grows in ``+Z``. Leads grow in ``-Z`` (down through the
board). All helpers add operations to a foundation ``Part`` and return it.
"""

from __future__ import annotations

from cadbuildr.foundation import (
    Circle,
    Extrusion,
    Part,
    Point,
    Rectangle,
    Sketch,
)


def add_box(
    part: Part,
    width: float,
    depth: float,
    height: float,
    cx: float = 0.0,
    cy: float = 0.0,
    z0: float = 0.0,
) -> Part:
    """Axis-aligned box centred at ``(cx, cy)`` spanning ``z0 .. z0+height``."""
    sketch = Sketch(part.xy())
    rect = Rectangle.from_center_and_sides(Point(sketch, cx, cy), width, depth)
    part.add_operation(Extrusion(rect, z0, z0 + height))
    return part


def add_cylinder_z(
    part: Part,
    radius: float,
    height: float,
    cx: float = 0.0,
    cy: float = 0.0,
    z0: float = 0.0,
) -> Part:
    """Vertical cylinder (axis along +Z) from ``z0`` to ``z0+height``."""
    sketch = Sketch(part.xy())
    circle = Circle(Point(sketch, cx, cy), radius)
    part.add_operation(Extrusion(circle, z0, z0 + height))
    return part


def add_cylinder_x(
    part: Part,
    radius: float,
    length: float,
    cy: float = 0.0,
    cz: float = 0.0,
    x0: float | None = None,
) -> Part:
    """Horizontal cylinder whose axis runs along +X.

    Sketched on the YZ plane (normal = X) and extruded along X. ``cy`` / ``cz``
    locate the axis; the cylinder is centred on X unless ``x0`` is given.
    """
    sketch = Sketch(part.yz())
    circle = Circle(Point(sketch, cy, cz), radius)
    if x0 is None:
        part.add_operation(Extrusion(circle, -length / 2.0, length / 2.0))
    else:
        part.add_operation(Extrusion(circle, x0, x0 + length))
    return part


def add_lead_z(part: Part, x: float, y: float, radius: float = 0.25, depth: float = 3.5) -> Part:
    """A round through-hole lead at ``(x, y)`` dropping from the board top
    (``z = 0``) down to ``z = -depth``."""
    sketch = Sketch(part.xy())
    circle = Circle(Point(sketch, x, y), radius)
    part.add_operation(Extrusion(circle, -depth, 0.0))
    return part


def add_pin_z(
    part: Part, x: float, y: float, side: float, top: float, bottom: float
) -> Part:
    """A square pin (e.g. a header post) at ``(x, y)`` spanning ``bottom..top``."""
    sketch = Sketch(part.xy())
    rect = Rectangle.from_center_and_sides(Point(sketch, x, y), side, side)
    part.add_operation(Extrusion(rect, bottom, top))
    return part
