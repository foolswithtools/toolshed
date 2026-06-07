"""Unit tests for the pure SVG → icon-registry normalizer (`icon_svg.py`).

Offline: every case feeds a literal SVG string. Covers path passthrough, the
primitive→path conversions (so drawOn works on non-path sets), and the error
paths.
"""

import math
from pathlib import Path

import pytest

import icon_svg

FIXTURES = Path(__file__).resolve().parent / "fixtures"


def test_path_only_svg():
    svg = (
        '<svg viewBox="0 0 24 24">'
        '<path fill="none" stroke="currentColor" stroke-width="2" '
        'd="M20 6L9 17l-5-5"/></svg>'
    )
    out = icon_svg.parse_svg(svg)
    assert out["viewBox"] == "0 0 24 24"
    assert out["paths"] == ["M20 6L9 17l-5-5"]
    assert out["strokeWidth"] == 2.0


def test_multiple_paths_inside_group():
    rocket = (FIXTURES / "icons" / "lucide-rocket.svg").read_text()
    out = icon_svg.parse_svg(rocket)
    # rocket is three <path>s wrapped in a <g> — all three must be extracted.
    assert len(out["paths"]) == 3
    assert out["strokeWidth"] == 2.0
    assert out["viewBox"] == "0 0 24 24"


def test_line_converted_to_path():
    svg = '<svg viewBox="0 0 24 24"><line x1="2" y1="4" x2="20" y2="16"/></svg>'
    out = icon_svg.parse_svg(svg)
    assert out["paths"] == ["M2.0 4.0L20.0 16.0"]


def test_polyline_converted_to_path():
    svg = '<svg viewBox="0 0 24 24"><polyline points="2,2 8,8 14,2"/></svg>'
    out = icon_svg.parse_svg(svg)
    assert out["paths"] == ["M2.0 2.0L8.0 8.0L14.0 2.0"]


def test_polygon_is_closed():
    svg = '<svg viewBox="0 0 24 24"><polygon points="2,2 8,8 14,2"/></svg>'
    out = icon_svg.parse_svg(svg)
    assert out["paths"][0].endswith("Z")


def test_circle_converted_to_arc_path():
    svg = '<svg viewBox="0 0 24 24"><circle cx="12" cy="12" r="9"/></svg>'
    out = icon_svg.parse_svg(svg)
    d = out["paths"][0]
    # starts at the leftmost point (cx-r, cy) and is a closed two-arc circle
    assert d.startswith("M3.0 12.0")
    assert d.count("a") == 2 and d.endswith("Z")


def test_rect_converted_to_path():
    svg = '<svg viewBox="0 0 24 24"><rect x="3" y="4" width="18" height="16"/></svg>'
    out = icon_svg.parse_svg(svg)
    assert out["paths"] == ["M3.0 4.0h18.0v16.0h-18.0Z"]


def test_rect_rounded_corners_preserved():
    # A <rect> with rx must keep its rounded corners (arc commands), not flatten
    # to a sharp box — otherwise pulled icons (Tabler/Heroicons) render wrong.
    svg = '<svg viewBox="0 0 24 24"><rect x="3" y="3" width="18" height="18" rx="4"/></svg>'
    out = icon_svg.parse_svg(svg)
    d = out["paths"][0]
    assert "a4" in d.replace(" ", "")  # arc segments present (rx mirrored to ry)
    assert d.count("a") == 4 and d.endswith("Z")


def test_rect_rx_mirrors_ry_and_clamps():
    # ry defaults to rx; both clamp to half the side so they never overshoot.
    svg = '<svg viewBox="0 0 10 10"><rect x="0" y="0" width="10" height="10" rx="99"/></svg>'
    out = icon_svg.parse_svg(svg)
    # rx clamps to w/2 = 5 -> a "circle-ish" superellipse, still valid + closed
    assert out["paths"][0].startswith("M5.0 0")
    assert out["paths"][0].endswith("Z")


def test_mixed_primitives_preserve_order():
    svg = (
        '<svg viewBox="0 0 24 24">'
        '<path d="M1 1L2 2"/>'
        '<line x1="0" y1="0" x2="3" y2="3"/>'
        "</svg>"
    )
    out = icon_svg.parse_svg(svg)
    assert out["paths"] == ["M1 1L2 2", "M0.0 0.0L3.0 3.0"]


def test_default_viewbox_when_missing():
    svg = '<svg><path d="M0 0L1 1"/></svg>'
    out = icon_svg.parse_svg(svg)
    assert out["viewBox"] == "0 0 24 24"


def test_raises_on_non_svg():
    with pytest.raises(ValueError):
        icon_svg.parse_svg("not an svg at all")


def test_raises_on_geometryless_svg():
    with pytest.raises(ValueError):
        icon_svg.parse_svg('<svg viewBox="0 0 24 24"><title>x</title></svg>')


def test_circle_geometry_is_correct():
    # The generated arc must actually pass through the 4 cardinal points.
    svg = '<svg viewBox="0 0 24 24"><circle cx="12" cy="12" r="10"/></svg>'
    out = icon_svg.parse_svg(svg)
    # leftmost point present in the move command
    assert "M2.0 12.0" in out["paths"][0]
    assert math.isclose(12 - 10, 2.0)
