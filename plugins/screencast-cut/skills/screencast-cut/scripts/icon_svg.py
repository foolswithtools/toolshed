#!/usr/bin/env python3
"""Pure SVG → icon-registry normalization.

Turns a raw `<svg>…</svg>` string into the shape the recipe engine consumes:
`{"viewBox": str, "paths": [str], "strokeWidth": float|None}`. Lucide (via the
Iconify API) is already `<path>`-only, but other permissive sets (Tabler,
Heroicons, …) still ship `<line>`/`<circle>`/`<polyline>`/`<rect>` primitives, so
we convert those to equivalent path `d`-strings. That keeps `drawOn` working on
every curated/pulled icon instead of letting a primitive-based icon silently
fail to animate.

PURE: no network, no I/O. The Iconify puller (`fetch_icon.py`) and the curated
floor generator both call `parse_svg` so a fetched icon and a bundled icon end
up structurally identical.
"""

import re

_VIEWBOX_RE = re.compile(r'viewBox\s*=\s*"([^"]+)"', re.IGNORECASE)
_STROKEWIDTH_RE = re.compile(r'stroke-width\s*=\s*"([^"]+)"', re.IGNORECASE)
_TAG_RE = re.compile(
    r"<(path|line|circle|ellipse|polyline|polygon|rect)\b([^>]*)>",
    re.IGNORECASE | re.DOTALL,
)


def _attr(attrs, name):
    m = re.search(rf'{name}\s*=\s*"([^"]*)"', attrs, re.IGNORECASE)
    return m.group(1) if m else None


def _num(s, default=0.0):
    try:
        return float(s)
    except (TypeError, ValueError):
        return default


def _points_to_path(points, close):
    nums = [p for p in re.split(r"[\s,]+", points.strip()) if p != ""]
    if len(nums) < 4:
        return None
    coords = [(_num(nums[i]), _num(nums[i + 1])) for i in range(0, len(nums) - 1, 2)]
    d = f"M{coords[0][0]} {coords[0][1]}" + "".join(
        f"L{x} {y}" for x, y in coords[1:]
    )
    return d + ("Z" if close else "")


def _circle_to_path(cx, cy, r):
    # Two semicircular arcs make a full circle that strokes cleanly (and so
    # draws-on smoothly via evolvePath).
    return (
        f"M{cx - r} {cy}"
        f"a{r} {r} 0 1 0 {2 * r} 0"
        f"a{r} {r} 0 1 0 {-2 * r} 0Z"
    )


def _ellipse_to_path(cx, cy, rx, ry):
    return (
        f"M{cx - rx} {cy}"
        f"a{rx} {ry} 0 1 0 {2 * rx} 0"
        f"a{rx} {ry} 0 1 0 {-2 * rx} 0Z"
    )


def _rect_to_path(x, y, w, h, rx=0.0, ry=0.0):
    # Sharp corners: the simple 4-segment box.
    if rx <= 0 and ry <= 0:
        return f"M{x} {y}h{w}v{h}h{-w}Z"
    # SVG rule: a missing rx/ry mirrors the other; both clamp to half the side.
    if rx <= 0:
        rx = ry
    if ry <= 0:
        ry = rx
    rx = min(rx, w / 2)
    ry = min(ry, h / 2)
    return (
        f"M{x + rx} {y}"
        f"h{w - 2 * rx}"
        f"a{rx} {ry} 0 0 1 {rx} {ry}"
        f"v{h - 2 * ry}"
        f"a{rx} {ry} 0 0 1 {-rx} {ry}"
        f"h{-(w - 2 * rx)}"
        f"a{rx} {ry} 0 0 1 {-rx} {-ry}"
        f"v{-(h - 2 * ry)}"
        f"a{rx} {ry} 0 0 1 {rx} {-ry}"
        "Z"
    )


def _element_to_path(tag, attrs):
    tag = tag.lower()
    if tag == "path":
        return _attr(attrs, "d")
    if tag == "line":
        x1, y1 = _num(_attr(attrs, "x1")), _num(_attr(attrs, "y1"))
        x2, y2 = _num(_attr(attrs, "x2")), _num(_attr(attrs, "y2"))
        return f"M{x1} {y1}L{x2} {y2}"
    if tag == "circle":
        return _circle_to_path(
            _num(_attr(attrs, "cx")), _num(_attr(attrs, "cy")), _num(_attr(attrs, "r"))
        )
    if tag == "ellipse":
        return _ellipse_to_path(
            _num(_attr(attrs, "cx")),
            _num(_attr(attrs, "cy")),
            _num(_attr(attrs, "rx")),
            _num(_attr(attrs, "ry")),
        )
    if tag == "polyline":
        pts = _attr(attrs, "points")
        return _points_to_path(pts, close=False) if pts else None
    if tag == "polygon":
        pts = _attr(attrs, "points")
        return _points_to_path(pts, close=True) if pts else None
    if tag == "rect":
        return _rect_to_path(
            _num(_attr(attrs, "x")),
            _num(_attr(attrs, "y")),
            _num(_attr(attrs, "width")),
            _num(_attr(attrs, "height")),
            _num(_attr(attrs, "rx")),
            _num(_attr(attrs, "ry")),
        )
    return None


def parse_svg(svg):
    """Normalize a raw SVG string into `{viewBox, paths, strokeWidth}`.

    Raises ValueError if the input has no parseable drawable geometry.
    """
    if not svg or "<svg" not in svg:
        raise ValueError("not an SVG document")

    vb_match = _VIEWBOX_RE.search(svg)
    view_box = vb_match.group(1).strip() if vb_match else "0 0 24 24"

    sw_match = _STROKEWIDTH_RE.search(svg)
    stroke_width = _num(sw_match.group(1), None) if sw_match else None

    paths = []
    for tag, attrs in _TAG_RE.findall(svg):
        d = _element_to_path(tag, attrs)
        if d and d.strip():
            paths.append(d.strip())

    if not paths:
        raise ValueError("SVG contained no drawable geometry")

    return {"viewBox": view_box, "paths": paths, "strokeWidth": stroke_width}
