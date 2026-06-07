"""Deterministic MOTION assertion for the animated-icon recipes (Phase 1.1).

The `golden-icons` filmstrip is a VISION pass — a human judges whether each
recipe looks right. But the deterministic gate (`verify_render`) only proves the
stills *render*, not that they *move*: a recipe that has fallen flat (drawn 100%
on every frame, a spinner stuck at one angle, a morph that never interpolates)
would still render a perfectly good still and slip through, leaning entirely on
the eye — the same shape as the earlier `ZoomedSection` gutter bug.

This test closes that. Each recipe gets its own single-primitive probe
composition (`motion-probe-<recipe>`, see videos/golden-icons/MotionProbe.tsx)
that animates over a 30-frame beat starting at frame 0, with NO <Loop>. So:

    frame 0  → animation start
    frame 15 → GUARANTEED mid-animation (progress 0.5; never a hold/plateau)
    frame 30 → settled end

We render those three frames and assert the stills are not all identical AND
that the mid frame differs from the start — proving the recipe is actually in
motion in its first half. Per-recipe isolation is what makes this meaningful: a
single broken recipe is caught on its own composition rather than hiding behind
the four others still moving in `golden-icons`.

Limitation (documented in RUBRIC.md V9): this catches "no motion", not
"wrong-but-still-moving recipe" — recipe *correctness* stays with the vision
pass. Renders are bit-deterministic, so identical pixels ⇒ identical bytes;
hashing the PNGs is a sound non-identity check.

Needs node + npm (same `golden_installed` fixture as the other e2e tests; skips
if absent).
"""

import hashlib
from pathlib import Path

import pytest

import verify_render as vr

# Mirrors MOTION_PROBES in videos/golden-icons/MotionProbe.tsx.
PROBE_IDS = [
    "motion-probe-drawOn",
    "motion-probe-popIn",
    "motion-probe-spin",
    "motion-probe-burst",
    "motion-probe-morph",
    "motion-probe-ripple",
]

# frame 0 = start, 15 = guaranteed mid-animation, 30 = settled end.
START, MID, END = 0, 15, 30


def _hash(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def _render_probe(project, comp_id, out_dir):
    """Render the start/mid/end stills for one probe; return {frame: sha256}."""
    result, raw_out, raw_err = vr._run_helper(
        project, comp_id, 0.5, [START, MID, END], out_dir
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
    for f in (START, MID, END):
        s = stills.get(f)
        assert s is not None, f"{comp_id}: frame {f} missing from helper output"
        assert s.get("ok"), f"{comp_id}: frame {f} failed to render: {s.get('error')}"
        out[f] = _hash(s["path"])
    return out


@pytest.mark.parametrize("comp_id", PROBE_IDS)
def test_recipe_actually_animates(golden_installed, comp_id, tmp_path):
    """start/mid/end stills are not all identical, and mid != start — the recipe
    is provably in motion (not frozen in a hold/plateau)."""
    project = golden_installed
    hashes = _render_probe(project, comp_id, tmp_path / comp_id)

    # A frozen/fallen-flat recipe renders the same still on every frame.
    assert len({hashes[START], hashes[MID], hashes[END]}) > 1, (
        f"{comp_id}: start/mid/end stills are byte-identical — the recipe is not "
        f"animating (frozen or fell back to a static state)."
    )
    # The guaranteed mid-animation frame must differ from the start: this is the
    # exact gap the vision-only gate could not catch.
    assert hashes[MID] != hashes[START], (
        f"{comp_id}: the mid-animation frame ({MID}) is identical to the start "
        f"frame ({START}) — nothing moved in the first half of the beat."
    )
