"""Guard the byte-identical-copies invariant for ALL shared scene-template files.

`scene-templates/<file>` is the single source of truth for the reusable scene
code (timing math, recipes, AnimatedIcon, ClickRipple, LottieIcon, the Safe*
wrappers). Each is copied VERBATIM into a video's `videos/<slug>/scenes/<file>`
at Phase 4. If the template changes but a copy isn't re-synced, that video
silently runs different code — the exact drift that shipped a stale 157-line
`timing.ts` once. This test makes any such drift a hard failure instead of
something you notice by reading line counts.

Scope: for every file that exists in BOTH `scene-templates/` and a given
video's `scenes/`, the two must be byte-identical. (A video need not contain
every template file; only the ones it actually uses are checked.)
"""

from pathlib import Path

SKILL_DIR = Path(__file__).resolve().parent.parent
TEMPLATES = SKILL_DIR / "scene-templates"
GOLDEN_VIDEOS = SKILL_DIR / "tests" / "fixtures" / "golden-project" / "videos"

# Files that are copied per-video (not the icons/ dir or per-video Root.tsx).
SHARED_FILES = [
    "timing.ts",
    "recipes.ts",
    "AnimatedIcon.tsx",
    "ClickRipple.tsx",
    "LottieIcon.tsx",
    "SafeImg.tsx",
    "SafeVideo.tsx",
    "VideoRun.tsx",
    "BlurredFrozenFrameCard.tsx",
]


def test_templates_exist():
    missing = [f for f in SHARED_FILES if not (TEMPLATES / f).is_file()]
    assert not missing, f"shared scene templates missing: {missing}"


def test_all_golden_scene_copies_match_template():
    stale = []
    checked = 0
    for scenes_dir in sorted(GOLDEN_VIDEOS.glob("*/scenes")):
        for name in SHARED_FILES:
            copy = scenes_dir / name
            tmpl = TEMPLATES / name
            if not (copy.is_file() and tmpl.is_file()):
                continue
            checked += 1
            if copy.read_text(encoding="utf-8") != tmpl.read_text(encoding="utf-8"):
                stale.append(str(copy.relative_to(SKILL_DIR)))
    assert checked > 0, "no golden scene copies found — fixture layout changed?"
    assert not stale, (
        "scene-template copies drifted from scene-templates/ — re-sync them "
        f"(copy the template over each): {stale}"
    )
