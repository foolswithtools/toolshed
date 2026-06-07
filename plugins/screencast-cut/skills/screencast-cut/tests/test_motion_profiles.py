"""Profile-level motion tunability: switching the active brand profile must be
able to change a sampled icon's motion.

`AnimatedIcon` reads its defaults from the active profile's `motion` block, so
two profiles that declare different `motion` defaults will render the same icon
with different motion. We assert the two shipped template profiles actually
differ (otherwise "theme-tunable" would be vacuous), and that each block carries
the four documented keys.
"""

import re
from pathlib import Path

import pytest

PLUGINS_ROOT = Path(__file__).resolve().parents[4]  # .../plugins
TEMPLATES = (
    PLUGINS_ROOT
    / "remotion-video"
    / "skills"
    / "remotion-video"
    / "templates"
)
DEFAULT_SG = TEMPLATES / "default" / "style-guide.ts"
BRAND_SG = TEMPLATES / "foolswithtools-brand" / "style-guide.ts"

_MOTION_RE = re.compile(r"export const motion\s*=\s*\{(.*?)\}\s*as const;", re.DOTALL)
_KEY_RE = re.compile(r"(\w+)\s*:\s*([^,\n]+)")


def _motion_block(path):
    text = path.read_text(encoding="utf-8")
    m = _MOTION_RE.search(text)
    assert m, f"no `motion` block found in {path}"
    body = m.group(1)
    # strip line comments so they don't get parsed as keys
    body = re.sub(r"//[^\n]*", "", body)
    out = {}
    for k, v in _KEY_RE.findall(body):
        out[k] = v.strip().strip('"')
    return out


EXPECTED_KEYS = {"defaultRecipe", "durationInFrames", "easing", "particleIntensity"}


def test_both_profiles_declare_motion_with_expected_keys():
    for sg in (DEFAULT_SG, BRAND_SG):
        block = _motion_block(sg)
        assert set(block) == EXPECTED_KEYS, f"{sg} motion keys = {set(block)}"


def test_profiles_differ_so_switching_changes_motion():
    default = _motion_block(DEFAULT_SG)
    brand = _motion_block(BRAND_SG)
    # The whole point of theme-tunable motion: a different active profile yields
    # different motion for the same icon. The default recipe itself differs here.
    assert default["defaultRecipe"] != brand["defaultRecipe"]
    assert default != brand


def test_default_profile_matches_global_floor():
    # The default template profile should not deviate from the documented global
    # config floor, so a fresh project's icons animate identically with or
    # without an explicit profile motion override.
    default = _motion_block(DEFAULT_SG)
    assert default["defaultRecipe"] == "drawOn"
    assert default["easing"] == "pop"
