"""Phase 4 — originated (owned) per-theme Lottie.

For each shipped demo theme we AUTHORED one signature Lottie motif, in that
theme's palette, and render it through the Phase-2 `@remotion/lottie` path. These
tests guard both halves of the deliverable:

  * OFFLINE (no node): every committed motif is expression-free (so it renders
    deterministically headlessly) and is authored in its theme's palette.
  * E2E (needs node): the `golden-theme-lottie` composition bundles and renders
    BOTH motifs for real; `verify_render` exits 0; and the render is
    deterministic AND actually animating (the property an expression-driven file
    would violate).
"""

import hashlib
import json
from pathlib import Path

import pytest

import lottie_ingest as li
import verify_render as vr

HERE = Path(__file__).resolve().parent
GOLDEN = HERE / "fixtures" / "golden-project"
LOTTIE_DIR = GOLDEN / "public" / "lottie"
TEMPLATE_LOTTIE_DIR = HERE.parent / "scene-templates" / "lottie"

WIDTH, HEIGHT = 1920, 1080
GOLDEN_THEME_LOTTIE_DURATION = 60
MAX_STILLS = 6

# Each motif → a signature [r,g,b,a] color (from the theme's style-guide.ts) that
# MUST appear in the file, proving it was authored directly in the theme palette.
THEME_MOTIFS = {
    "default-orbit.json": [0.133333, 0.827451, 0.933333, 1],  # cyan #22d3ee
    "foolswithtools-spark.json": [0.8, 1.0, 0.0, 1],           # acid #CCFF00
}


def _load(path):
    return json.loads(Path(path).read_text())


def _hash(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def _all_colors(node):
    """Yield every flat-fill/stroke color array in a Lottie tree."""
    if isinstance(node, dict):
        if node.get("ty") in ("fl", "st"):
            c = node.get("c", {})
            if isinstance(c, dict) and "k" in c:
                yield c["k"]
        for v in node.values():
            yield from _all_colors(v)
    elif isinstance(node, list):
        for v in node:
            yield from _all_colors(v)


# --------------------------------------------------------------------------- #
# Offline: the files themselves are sound (no node required).
# --------------------------------------------------------------------------- #

@pytest.mark.parametrize("fname", sorted(THEME_MOTIFS))
def test_motif_committed_in_both_locations(fname):
    """The shippable template copy and the golden render copy are byte-identical
    (both emitted by gen_theme_lottie.py — no drift)."""
    tpl = TEMPLATE_LOTTIE_DIR / fname
    gold = LOTTIE_DIR / fname
    assert tpl.is_file(), f"missing shippable motif {tpl}"
    assert gold.is_file(), f"missing golden motif {gold}"
    assert tpl.read_text() == gold.read_text(), f"{fname} drifted between copies"


@pytest.mark.parametrize("fname", sorted(THEME_MOTIFS))
def test_motif_is_lottie_and_expression_free(fname):
    """Owned per-theme motif must look like Lottie and carry NO AE expressions —
    the determinism precondition for the headless render path."""
    data = _load(LOTTIE_DIR / fname)
    assert li.looks_like_lottie(data)
    # Raises LottieIngestError if any expression is present.
    li.assert_no_expressions(data)


@pytest.mark.parametrize("fname,color", sorted(THEME_MOTIFS.items()))
def test_motif_uses_theme_palette(fname, color):
    """The signature theme color is present — the motif was authored directly in
    the theme palette (the whole point of an originated per-theme Lottie: no
    recolor pass)."""
    data = _load(LOTTIE_DIR / fname)
    colors = [c for c in _all_colors(data)]
    # Compare with tolerance on the rounded floats.
    found = any(
        len(c) >= 3 and all(abs(c[i] - color[i]) < 1e-3 for i in range(3))
        for c in colors
    )
    assert found, f"{fname} does not contain its theme signature color {color}"


# --------------------------------------------------------------------------- #
# E2E: the golden composition renders both motifs for real.
# --------------------------------------------------------------------------- #

def test_golden_theme_lottie_renders_and_verifies(golden_installed):
    """Both originated motifs bundle and render through LottieIcon; verify exits 0."""
    project = golden_installed
    rc = vr.main([
        str(project), "golden-theme-lottie",
        "--expect-duration-frames", str(GOLDEN_THEME_LOTTIE_DURATION),
        "--expect-width", str(WIDTH),
        "--expect-height", str(HEIGHT),
        "--scale", "0.5",
        "--max-stills", str(MAX_STILLS),
    ])
    assert rc == 0, "verify_render did not exit 0 on golden-theme-lottie"

    summary = _load(
        project / "videos" / "golden-theme-lottie" / ".checks" / "verify-summary.json"
    )
    assert summary["status"] == "pass"
    assert summary["gates"]["bundle"]["pass"]
    assert summary["gates"]["composition_exists"]["pass"]
    assert summary["gates"]["dimensions"]["pass"]
    assert summary["gates"]["duration"]["pass"]
    assert summary["gates"]["duration"]["actual"] == GOLDEN_THEME_LOTTIE_DURATION
    assert summary["gates"]["stills_render"]["pass"]
    assert summary["gates"]["stills_render"]["count"] > 0
    assert all(s["rendered"] for s in summary["filmstrip"]), \
        "a golden-theme-lottie filmstrip still failed to render"


def _still(result, frame):
    s = next(s for s in result["stills"] if s["frame"] == frame)
    assert s["ok"], f"frame {frame} failed: {s.get('error')}"
    return s["path"]


def test_golden_theme_lottie_is_deterministic_and_animates(golden_installed, tmp_path):
    """The originated per-theme Lottie renders DETERMINISTICALLY (same frame →
    identical bytes across renders — an expression-driven file would flicker) AND
    actually animates (two frames differ). Both motifs share one composition, so
    this gates them together."""
    project = golden_installed
    # frame 9 twice, frame 24 once: 9 and 24 are both mid-loop for the 60-frame
    # rotation, guaranteed to differ.
    r1, _, e1 = vr._run_helper(project, "golden-theme-lottie", 0.5, [9], tmp_path / "run1")
    r2, _, e2 = vr._run_helper(project, "golden-theme-lottie", 0.5, [9, 24], tmp_path / "run2")
    assert r1 and r1.get("ok"), f"render 1 failed: {e1}"
    assert r2 and r2.get("ok"), f"render 2 failed: {e2}"

    f9a = _hash(_still(r1, 9))
    f9b = _hash(_still(r2, 9))
    f24 = _hash(_still(r2, 24))

    assert f9a == f9b, "golden-theme-lottie frame 9 differs between renders — NOT deterministic"
    assert f9a != f24, "golden-theme-lottie frame 9 == frame 24 — the Lottie is not animating"
