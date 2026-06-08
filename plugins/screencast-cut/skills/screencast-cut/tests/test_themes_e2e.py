"""End-to-end gate for the per-theme example animation packs (Phase 3).

Two things are proven here, both for real (bundle + render via the shared
`verify_render` harness; skips if node/npm are absent, like the other e2e
tests):

1. The `golden-themes` showcase composition — the same example pack rendered
   under every shipped demo theme, side-by-side — bundles and renders, and
   `verify_render` exits 0 with status pass.

2. Theme-tunability is *demonstrated, not just asserted*: the two per-theme PROBE
   compositions (`theme-pack-default`, `theme-pack-foolswithtools-brand`) render
   the IDENTICAL pack on a neutral background with an identical icon color — so
   the only thing that can differ between them is the motion itself (recipe /
   easing / particle intensity / duration, driven by each theme's `motion`
   block). We render a shared mid-animation frame of each and assert the stills
   are NOT byte-identical. Because the palette is held constant, a difference can
   only be motion. We also assert each probe actually animates (start != mid),
   so a frozen pack can't pass by being trivially "different but static".
"""

import hashlib
from pathlib import Path

import pytest

import verify_render as vr

WIDTH, HEIGHT, FPS = 1920, 1080, 30

GOLDEN_THEMES_DURATION = 120
GOLDEN_THEMES_MAX_STILLS = 6

# Mirrors THEME_PROBES in videos/golden-themes/ThemePack.tsx.
THEME_PROBE_IDS = ["theme-pack-default", "theme-pack-foolswithtools-brand"]

# frame 0 = start, 13 = guaranteed mid-animation for both themes (default beat
# 30, brand beat 26 → both still animating at 13), 30 = settled.
START, MID = 0, 13


def _load(path):
    import json
    return json.loads(Path(path).read_text())


def _hash(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def test_golden_themes_renders_and_verifies(golden_installed):
    """The side-by-side per-theme showcase bundles and renders for real."""
    project = golden_installed
    rc = vr.main([
        str(project), "golden-themes",
        "--expect-duration-frames", str(GOLDEN_THEMES_DURATION),
        "--expect-width", str(WIDTH),
        "--expect-height", str(HEIGHT),
        "--scale", "0.5",
        "--max-stills", str(GOLDEN_THEMES_MAX_STILLS),
        "--video-start-frame", "0",
    ])
    assert rc == 0, "verify_render did not exit 0 on golden-themes"

    summary = _load(
        project / "videos" / "golden-themes" / ".checks" / "verify-summary.json"
    )
    assert summary["status"] == "pass"
    assert summary["gates"]["bundle"]["pass"]
    assert summary["gates"]["composition_exists"]["pass"]
    assert summary["gates"]["dimensions"]["pass"]
    assert summary["gates"]["duration"]["pass"]
    assert summary["gates"]["duration"]["actual"] == GOLDEN_THEMES_DURATION
    assert summary["gates"]["stills_render"]["pass"]
    assert summary["gates"]["stills_render"]["count"] > 0
    assert all(s["rendered"] for s in summary["filmstrip"]), \
        "a golden-themes filmstrip still failed to render"


def _probe_hashes(project, comp_id, tmp_path):
    """Render START/MID stills for one theme probe; return {frame: sha256}."""
    result, raw_out, raw_err = vr._run_helper(
        project, comp_id, 0.5, [START, MID], tmp_path / comp_id
    )
    assert result is not None, (
        f"verify helper produced no result for {comp_id}.\n"
        f"stdout:\n{raw_out}\nstderr:\n{raw_err}"
    )
    assert not result.get("envError"), f"environment error: {result.get('error')}"
    assert result.get("ok"), (
        f"{comp_id} failed to bundle/find composition: "
        f"{result.get('stage')} / {result.get('error')}"
    )
    stills = {s["frame"]: s for s in result.get("stills", [])}
    out = {}
    for f in (START, MID):
        s = stills.get(f)
        assert s is not None, f"{comp_id}: frame {f} missing from helper output"
        assert s.get("ok"), f"{comp_id}: frame {f} failed to render: {s.get('error')}"
        out[f] = _hash(s["path"])
    return out


def test_themes_differ_so_switching_changes_motion(golden_installed, tmp_path):
    """Switching the theme visibly changes the SAME pack's motion.

    The probes hold palette constant (neutral bg + identical icon color), so a
    byte difference between the two themes' mid-animation stills can only come
    from the motion block. Each probe must also animate (start != mid), ruling
    out a frozen-but-coincidentally-different pass.
    """
    project = golden_installed
    by_theme = {
        cid: _probe_hashes(project, cid, tmp_path) for cid in THEME_PROBE_IDS
    }

    # Each theme's pack is actually in motion in its first half.
    for cid, h in by_theme.items():
        assert h[MID] != h[START], (
            f"{cid}: mid-animation frame ({MID}) is identical to start ({START}) "
            f"— the pack is not animating."
        )

    # The two themes render the same pack DIFFERENTLY at the same frame. Palette
    # is held constant across probes, so this difference is purely motion.
    d = by_theme["theme-pack-default"][MID]
    b = by_theme["theme-pack-foolswithtools-brand"][MID]
    assert d != b, (
        "the two themes' packs are byte-identical at the mid-animation frame — "
        "switching the theme did NOT change the motion (theme `motion` blocks "
        "are not driving the pack)."
    )
