"""Guard the byte-identical-copies invariant for the timing twin.

`scene-templates/timing.ts` is the single source of truth for the frame math;
it is copied VERBATIM into every per-video `videos/<slug>/scenes/timing.ts` at
Phase 4. If the template grows (e.g. new motion primitives) but a copy isn't
re-synced, the copy silently goes stale — a project would then run different
math depending on which video it is. This test makes that drift a hard failure
instead of a thing you discover by reading line counts.
"""

from pathlib import Path

SKILL_DIR = Path(__file__).resolve().parent.parent
TEMPLATE = SKILL_DIR / "scene-templates" / "timing.ts"
GOLDEN_VIDEOS = SKILL_DIR / "tests" / "fixtures" / "golden-project" / "videos"


def test_template_exists():
    assert TEMPLATE.is_file(), f"missing timing template: {TEMPLATE}"


def test_all_golden_timing_copies_match_template():
    expected = TEMPLATE.read_text(encoding="utf-8")
    copies = sorted(GOLDEN_VIDEOS.glob("*/scenes/timing.ts"))
    assert copies, "no golden timing.ts copies found — fixture layout changed?"
    stale = [
        str(c.relative_to(SKILL_DIR))
        for c in copies
        if c.read_text(encoding="utf-8") != expected
    ]
    assert not stale, (
        "timing.ts copies drifted from scene-templates/timing.ts — re-sync them "
        f"(copy the template over each): {stale}"
    )
